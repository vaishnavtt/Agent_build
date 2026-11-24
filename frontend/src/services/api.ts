/**
 * AgentForge AI - Reusable Backend API Communication Functions
 * Connects React Frontend with FastAPI Backend endpoints.
 */

const API_BASE = 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  let response: Response;
  try {
    response = await fetch(endpoint, { ...options, headers });
  } catch (primaryErr) {
    // If relative fetch fails (e.g. running in standalone dev server), try absolute API_BASE URL
    if (!endpoint.startsWith('http')) {
      response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } else {
      throw primaryErr;
    }
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const workflowApi = {
  /**
   * Health Check
   */
  async checkHealth(): Promise<{ status: string; database: string }> {
    return request('/api/v1/health');
  },

  /**
   * Retrieve all saved workflows from SQLite
   */
  async getWorkflows(): Promise<any[]> {
    try {
      return await request('/api/workflows');
    } catch {
      return await request('/api/v1/workflows');
    }
  },

  /**
   * Retrieve a specific workflow by ID
   */
  async getWorkflow(workflowId: string): Promise<any> {
    try {
      return await request(`/api/workflows/${workflowId}`);
    } catch {
      return await request(`/api/v1/workflows/${workflowId}`);
    }
  },

  /**
   * Create and save a new workflow in SQLite
   */
  async createWorkflow(payload: {
    name?: string;
    workflow_name?: string;
    description?: string;
    nodes?: any[];
    edges?: any[];
    workflow_data?: any;
    configuration?: any;
    tags?: string[];
  }): Promise<any> {
    try {
      return await request('/api/workflows', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch {
      return await request('/api/v1/workflows', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    }
  },

  /**
   * Update an existing workflow in SQLite
   */
  async updateWorkflow(workflowId: string, payload: any): Promise<any> {
    try {
      return await request(`/api/workflows/${workflowId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    } catch {
      return await request(`/api/v1/workflows/${workflowId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    }
  },

  /**
   * Delete a workflow by ID
   */
  async deleteWorkflow(workflowId: string): Promise<void> {
    try {
      await request(`/api/workflows/${workflowId}`, { method: 'DELETE' });
    } catch {
      await request(`/api/v1/workflows/${workflowId}`, { method: 'DELETE' });
    }
  },

  /**
   * Execute a saved workflow and record history in SQLite
   */
  async runWorkflow(workflowId: string, inputPayload?: any, autoRepair: boolean = true): Promise<any> {
    try {
      return await request(`/api/workflows/${workflowId}/run`, {
        method: 'POST',
        body: JSON.stringify({ input_payload: inputPayload, auto_repair: autoRepair }),
      });
    } catch {
      return await request(`/api/v1/workflows/${workflowId}/run`, {
        method: 'POST',
        body: JSON.stringify({ input_payload: inputPayload, auto_repair: autoRepair }),
      });
    }
  },

  /**
   * Execute an adhoc workflow graph directly from the canvas
   */
  async runAdhocWorkflow(payload: {
    name?: string;
    nodes: any[];
    edges: any[];
    input_payload?: any;
    auto_repair?: boolean;
  }): Promise<any> {
    return request('/api/v1/workflows/run-adhoc', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Validate a specific saved workflow's structure and connections
   */
  async validateSavedWorkflow(workflowId: string, payload?: { nodes?: any[]; edges?: any[] }): Promise<any> {
    try {
      return await request(`/api/workflows/${workflowId}/validate`, {
        method: 'POST',
        body: JSON.stringify(payload || {}),
      });
    } catch {
      return await request(`/api/v1/workflows/${workflowId}/validate`, {
        method: 'POST',
        body: JSON.stringify(payload || {}),
      });
    }
  },

  /**
   * Validate arbitrary nodes and edges graph structure
   */
  async validateGraph(nodes: any[], edges: any[]): Promise<any> {
    try {
      return await request('/api/workflows/validate', {
        method: 'POST',
        body: JSON.stringify({ nodes, edges }),
      });
    } catch {
      return await request('/api/v1/workflows/validate', {
        method: 'POST',
        body: JSON.stringify({ nodes, edges }),
      });
    }
  },

  /**
   * Retrieve execution history for a specific workflow
   */
  async getWorkflowHistory(workflowId: string): Promise<any[]> {
    try {
      return await request(`/api/workflows/${workflowId}/history`);
    } catch {
      return await request(`/api/v1/workflows/${workflowId}/executions`);
    }
  },

  /**
   * Retrieve specific execution record details
   */
  async getExecutionDetails(executionId: string): Promise<any> {
    try {
      return await request(`/api/executions/${executionId}`);
    } catch {
      return await request(`/api/v1/executions/${executionId}`);
    }
  },
};
