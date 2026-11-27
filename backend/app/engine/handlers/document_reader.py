import io
import base64
from typing import Dict, Any, List
import pypdf
from app.engine.handlers.base import BaseNodeHandler, get_node_meta
from app.engine.security import validate_document_path
from app.engine.types import ExecutionContext, NodeExecutionError


class DocumentReaderNodeHandler(BaseNodeHandler):
    """Extracts text, metadata, and chunked sections from PDF and text documents."""

    def __init__(self):
        super().__init__("Document Reader")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        node_id, node_name, config = get_node_meta(node, "Document Reader")

        chunk_size = int(config.get("chunkSize", 1000))
        chunk_overlap = int(config.get("chunkOverlap", 200))

        # Look for PDF file path or byte data
        file_source = (
            incoming_data.get("filePath")
            or incoming_data.get("file_path")
            or incoming_data.get("file")
            or incoming_data.get("url")
            or config.get("filePath")
            or config.get("file_path")
        )

        pdf_bytes = None
        plain_text = None

        if isinstance(file_source, bytes):
            pdf_bytes = file_source
        elif isinstance(file_source, str) and file_source.startswith("data:application/pdf;base64,"):
            b64_data = file_source.split("base64,", 1)[1]
            try:
                pdf_bytes = base64.b64decode(b64_data)
            except Exception as e:
                raise NodeExecutionError(
                    f"Failed to decode base64 PDF in node '{node_name}': {str(e)}",
                    node_id=node_id,
                )
        elif isinstance(file_source, str) and file_source.strip():
            safe_path = validate_document_path(file_source.strip(), node_id=node_id, node_name=node_name)
            try:
                raw_bytes = safe_path.read_bytes()
            except Exception as e:
                raise NodeExecutionError(
                    f"Failed reading file at '{safe_path.name}': {str(e)}",
                    node_id=node_id,
                )
            if safe_path.suffix.lower() in (".txt", ".md", ".json", ".csv"):
                plain_text = raw_bytes.decode("utf-8", errors="replace")
            else:
                pdf_bytes = raw_bytes
        else:
            # Check if text was passed directly
            direct_text = incoming_data.get("content") or incoming_data.get("text")
            if direct_text:
                return {
                    "content": str(direct_text),
                    "text": str(direct_text),
                    "output": str(direct_text),
                    "pages": 1,
                    "metadata": {"source": "direct_text"},
                    "chunks": [str(direct_text)],
                }
            raise NodeExecutionError(
                f"No PDF file path or content provided to Document Reader node '{node_name}'.",
                node_id=node_id,
            )

        if plain_text is not None:
            chunks = self._chunk_text(plain_text, chunk_size, chunk_overlap)
            return {
                "content": plain_text,
                "text": plain_text,
                "output": plain_text,
                "pages": 1,
                "chunks": chunks,
                "metadata": {"source": "text_file"},
            }

        if not pdf_bytes or len(pdf_bytes) == 0:
            raise NodeExecutionError(
                f"PDF file is empty (0 bytes) in node '{node_name}'.",
                node_id=node_id,
            )

        # Parse with pypdf
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise NodeExecutionError(
                f"Corrupted or unreadable PDF document in node '{node_name}': {str(e)}",
                node_id=node_id,
            )

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise NodeExecutionError(
                f"PDF document has 0 pages in node '{node_name}'.",
                node_id=node_id,
            )

        extracted_pages = []
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text)
            except Exception as e:
                extracted_pages.append(f"[Page {i+1} extraction failed: {str(e)}]")

        full_text = "\n\n".join(extracted_pages).strip()
        chunks = self._chunk_text(full_text, chunk_size, chunk_overlap)

        metadata_dict = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                metadata_dict[str(k).replace("/", "")] = str(v)

        return {
            "content": full_text,
            "text": full_text,
            "output": full_text,
            "pages": num_pages,
            "chunks": chunks,
            "metadata": metadata_dict,
        }

    def _chunk_text(self, full_text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        chunks: List[str] = []
        if full_text:
            step = max(1, chunk_size - chunk_overlap)
            for i in range(0, len(full_text), step):
                chunks.append(full_text[i : i + chunk_size])
        return chunks
