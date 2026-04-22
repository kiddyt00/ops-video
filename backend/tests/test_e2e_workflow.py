#!/usr/bin/env python3
"""
End-to-End Workflow Test Script

Tests the complete workflow from script generation to video composition:
1. Create a project
2. Generate script (LLM)
3. Generate storyboard (LLM)
4. Generate images (ComfyUI or mock)
5. Generate audio (TTS + BGM)
6. Compose video

Run with: python tests/test_e2e_workflow.py
"""

import asyncio
import sys
import time
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_TOPIC = "一个关于勇气的冒险故事"
TEST_STYLE = "comic"
TEST_DURATION = "1 minute"


class E2ETestRunner:
    """End-to-end test runner for complete workflow"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.project_id: str | None = None
        self.results: dict = {
            "project_id": None,
            "script_task_id": None,
            "storyboard_task_id": None,
            "image_task_id": None,
            "audio_task_id": None,
            "video_task_id": None,
            "errors": [],
        }

    async def health_check(self) -> bool:
        """Check if backend is running"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def create_project(self) -> str:
        """Create a test project"""
        print("\n[1/7] Creating project...")
        response = await self.client.post(
            "/projects",
            json={
                "name": f"E2E Test {int(time.time())}",
                "description": "End-to-end workflow test",
            },
        )
        response.raise_for_status()
        data = response.json()
        self.project_id = data["id"]
        self.results["project_id"] = data["id"]
        print(f"  Created project: {data['id']}")
        return data["id"]

    async def generate_script(self) -> str:
        """Generate script using LLM"""
        print("\n[2/7] Generating script...")
        response = await self.client.post(
            f"/workflow/{self.project_id}/advance/script",
            json={
                "topic": TEST_TOPIC,
                "style": TEST_STYLE,
                "duration": TEST_DURATION,
            },
        )
        response.raise_for_status()
        data = response.json()
        self.results["script_task_id"] = data["task_id"]
        print(f"  Script task created: {data['task_id']}")
        print(f"  Status: {data.get('status', 'unknown')}")
        return data["task_id"]

    async def generate_storyboard(self, script_file_id: str = None) -> str:
        """Generate storyboard from script"""
        print("\n[3/7] Generating storyboard...")
        params = {
            "panel_count": 4,
        }
        if script_file_id:
            params["script_file_id"] = script_file_id

        response = await self.client.post(
            f"/workflow/{self.project_id}/advance/storyboard",
            json=params,
        )
        response.raise_for_status()
        data = response.json()
        self.results["storyboard_task_id"] = data["task_id"]
        print(f"  Storyboard task created: {data['task_id']}")
        return data["task_id"]

    async def generate_images(self, prompt: str = "test scene") -> str:
        """Generate images from storyboard"""
        print("\n[4/7] Generating images...")
        response = await self.client.post(
            f"/workflow/{self.project_id}/advance/image",
            json={
                "prompt": prompt,
                "negative_prompt": "low quality, blurry",
                "steps": 4,  # Low steps for faster testing
                "width": 64,  # Small size for faster testing
                "height": 96,
            },
        )
        response.raise_for_status()
        data = response.json()
        self.results["image_task_id"] = data["task_id"]
        print(f"  Image task created: {data['task_id']}")
        return data["task_id"]

    async def generate_audio(self, texts: list[str] = None) -> str:
        """Generate TTS and BGM"""
        print("\n[5/7] Generating audio...")
        params = {
            "voice": "zh-CN-XiaoxiaoNeural",
            "generate_bgm": True,
            "bgm_mood": "ambient",
        }
        if texts:
            params["texts"] = texts

        response = await self.client.post(
            f"/workflow/{self.project_id}/advance/audio",
            json=params,
        )
        response.raise_for_status()
        data = response.json()
        self.results["audio_task_id"] = data["task_id"]
        print(f"  Audio task created: {data['task_id']}")
        return data["task_id"]

    async def compose_video(self, panels: list[dict] = None) -> str:
        """Compose final video"""
        print("\n[6/7] Composing video...")
        params = {
            "resolution": [512, 768],  # Small size for faster testing
            "fps": 12,
            "generate_bgm": True,
        }
        if panels:
            params["panels"] = panels

        response = await self.client.post(
            f"/workflow/{self.project_id}/advance/video",
            json=params,
        )
        response.raise_for_status()
        data = response.json()
        self.results["video_task_id"] = data["task_id"]
        print(f"  Video task created: {data['task_id']}")
        return data["task_id"]

    async def wait_for_task(self, task_id: str, timeout: int = 120) -> dict:
        """Wait for task to complete"""
        start = time.time()
        while time.time() - start < timeout:
            response = await self.client.get(f"/tasks/{task_id}")
            response.raise_for_status()
            task = response.json()
            status = task.get("status")

            if status in ["completed", "failed", "cancelled"]:
                return task

            print(f"  Task {task_id} status: {status}...")
            await asyncio.sleep(2)

        raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")

    async def get_workflow_status(self) -> dict:
        """Get workflow status"""
        print("\n[Status] Getting workflow status...")
        response = await self.client.get(f"/workflow/{self.project_id}/status")
        response.raise_for_status()
        return response.json()

    async def cleanup(self):
        """Cleanup test project"""
        if self.project_id:
            print(f"\n[Cleanup] Deleting project {self.project_id}...")
            await self.client.delete(f"/projects/{self.project_id}")

    async def run_full_workflow(self, skip_video: bool = False) -> dict:
        """Run complete workflow and return results"""
        print("=" * 60)
        print("OPS-VIDEO End-to-End Workflow Test")
        print("=" * 60)

        # Health check
        print("\n[0/7] Checking backend health...")
        if not await self.health_check():
            raise RuntimeError("Backend is not running or unhealthy")
        print("  Backend is healthy")

        try:
            # Create project
            await self.create_project()

            # Generate script
            await self.generate_script()

            # Generate storyboard
            await self.generate_storyboard()

            # Generate images (using small size for fast testing)
            await self.generate_images(prompt="anime style character, simple background")

            # Generate audio
            await self.generate_audio(texts=["你好，世界！", "这是一个冒险故事。"])

            # Compose video (optional, takes longer)
            if not skip_video:
                await self.compose_video()

            # Get final status
            status = await self.get_workflow_status()
            print("\n" + "=" * 60)
            print("Workflow Status:")
            for stage in status.get("stages", []):
                print(f"  {stage['stage']}: {stage['status']} "
                      f"({stage['completed_tasks']}/{stage['total_tasks']})")

            self.results["final_status"] = status
            return self.results

        except Exception as e:
            self.results["errors"].append(str(e))
            print(f"\nError: {e}")
            raise

        finally:
            # Uncomment to auto-cleanup
            # await self.cleanup()
            await self.client.aclose()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="E2E Workflow Test")
    parser.add_argument("--skip-video", action="store_true", help="Skip video composition step")
    parser.add_argument("--url", default=API_BASE_URL, help="Backend API URL")
    parser.add_argument("--output", help="Output results to file")
    args = parser.parse_args()

    runner = E2ETestRunner(base_url=args.url)

    try:
        results = await runner.run_full_workflow(skip_video=args.skip_video)

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Project ID: {results['project_id']}")
        print(f"Script Task: {results['script_task_id']}")
        print(f"Storyboard Task: {results['storyboard_task_id']}")
        print(f"Image Task: {results['image_task_id']}")
        print(f"Audio Task: {results['audio_task_id']}")
        if results['video_task_id']:
            print(f"Video Task: {results['video_task_id']}")

        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for err in results['errors']:
                print(f"  - {err}")
        else:
            print("Errors: 0")

        # Save results
        if args.output:
            import json
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {args.output}")

        # Exit with error if there were errors
        sys.exit(1 if results['errors'] else 0)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
