#!/usr/bin/env python3
"""Generate Wanx images for the storyboard panels."""
import os, sys, json, asyncio, re
from pathlib import Path
os.environ['MOCK_MODE'] = 'false'
sys.path.insert(0, '.')
from app.config import settings
from app.providers.wanx_provider import WanxProvider

sb_text = Path('storage/scripts/script_79e6f583.txt').read_text()
sb_text = re.sub(r'^```json\s*\n', '', sb_text)
sb_text = re.sub(r'\n```\s*$', '', sb_text)
sb = json.loads(sb_text)

async def main():
    p = WanxProvider()
    for i, panel in enumerate(sb['panels']):
        desc = panel['scene_description'][:250]
        prompt = f'{desc}。童话风格，动漫插画，柔和色彩，精美细节，电影级光影。'
        print(f'Panel {panel["panel_number"]}: {prompt[:80]}...')
        result = await p.generate({
            'prompt': prompt,
            'size': '1024*1024',
            'n': 1,
            'negative_prompt': '丑陋，扭曲，低画质，模糊，文字，水印',
            'prompt_extend': True,
        })
        if result.success:
            for fp in result.file_paths:
                print(f'  ✅ {fp.name} ({fp.stat().st_size}B)')
        else:
            print(f'  ❌ {result.error_message[:120]}')
        if i < len(sb['panels']) - 1:
            await asyncio.sleep(1)
    print(f'\n✅ {len(sb["panels"])} panels done!')

asyncio.run(main())
