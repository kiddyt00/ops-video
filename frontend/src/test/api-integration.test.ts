/**
 * API Integration Tests
 *
 * Tests that verify frontend API clients can correctly call backend APIs.
 * These tests require the backend to be running at http://localhost:8000
 *
 * Run with: npm run test:api
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { api } from '@/lib/api'
import { projectApi } from '@/lib/api/projects'
import { taskApi } from '@/lib/api/tasks'
import { workflowApi } from '@/lib/api/workflow'
import { generatorApi } from '@/lib/api/generators'
import type { Project } from '@/types/project'

// Test configuration
const TEST_API_URL = process.env.TEST_API_URL || 'http://localhost:8000/api/v1'

// Test data
let testProjectId: string

describe('API Integration Tests', () => {
  beforeAll(async () => {
    // Configure API base URL for tests
    api.defaults.baseURL = TEST_API_URL
  })

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const response = await api.get('/health')
      expect(response.data.status).toBe('healthy')
    })

    it('should return app info at root', async () => {
      const response = await api.get('/')
      expect(response.data.name).toBe('Ops-Video')
    })
  })

  describe('Projects API', () => {
    const createdProjectIds: string[] = []

    afterAll(async () => {
      // Cleanup created projects
      for (const id of createdProjectIds) {
        try {
          await projectApi.remove(id)
        } catch {
          // Ignore cleanup errors
        }
      }
    })

    it('should list projects', async () => {
      const projects = await projectApi.list()
      expect(Array.isArray(projects)).toBe(true)
    })

    it('should create a project', async () => {
      const project = await projectApi.create({
        name: `Test Project ${Date.now()}`,
        description: 'Integration test project',
      })

      expect(project.id).toBeDefined()
      expect(project.name).toContain('Test Project')

      testProjectId = project.id
      createdProjectIds.push(project.id)
    })

    it('should get project by id', async () => {
      if (!testProjectId) return

      const project = await projectApi.get(testProjectId)
      expect(project.id).toBe(testProjectId)
    })

    it('should update project', async () => {
      if (!testProjectId) return

      const updated = await projectApi.update(testProjectId, {
        description: 'Updated description',
      })

      expect(updated.description).toBe('Updated description')
    })
  })

  describe('Workflow API', () => {
    it('should get workflow status', async () => {
      if (!testProjectId) return

      const status = await workflowApi.getStatus(testProjectId)
      expect(status.project_id).toBeDefined()
      expect(status.stages).toBeDefined()
      expect(Array.isArray(status.stages)).toBe(true)
    })

    it('should get workflow history', async () => {
      if (!testProjectId) return

      const history = await workflowApi.getHistory(testProjectId)
      expect(history.project_id).toBeDefined()
      expect(history.history).toBeDefined()
    })

    it('should advance workflow to script stage', async () => {
      if (!testProjectId) return

      const result = await workflowApi.advanceToStage(testProjectId, 'script', {
        topic: 'Test story',
        style: 'comic',
        duration: '1 minute',
      })

      expect(result.task_id).toBeDefined()
      expect(result.stage).toBe('script')
    })
  })

  describe('Generators API', () => {
    it('should list available generators', async () => {
      const generators = await generatorApi.list()
      expect(Array.isArray(generators)).toBe(true)
      expect(generators.length).toBeGreaterThan(0)
    })

    it('should get generator info', async () => {
      const generator = await generatorApi.get('script')
      expect(generator.name).toBe('Script Generator')
      expect(generator.type).toBe('llm')
    })
  })

  describe('Tasks API', () => {
    it('should list tasks for project', async () => {
      if (!testProjectId) return

      const tasks = await taskApi.list(testProjectId)
      expect(Array.isArray(tasks)).toBe(true)
    })
  })
})
