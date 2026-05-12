# ops-video 剩余任务计划

> 更新时间: 2026-05-12
> 当前状态: NovelForge 全流程 (灵感→故事→大纲→剧本→分镜→生图→配音→成片) 已跑通
> 8阶段全链路可工作，前后端联调完成

---

## 已完成 (Phase 1-19)

- ✅ Phase 1-16: 基础架构、工作流、前端、测试
- ✅ Phase 17: NovelForge 工作流扩展 (8阶段)
- ✅ Phase 18: LLM 配置数据库化
- ✅ Phase 19: 技术债务清理 (datetime/枚举/表结构/AI模型激活)
- ✅ 6步交互式故事创作向导 (StoryWizard)
- ✅ 后端生成后写入 Story DB 表
- ✅ variant_group selected_file 自动设置
- ✅ chapters API (从 Story chapter_outline 读取)
- ✅ Tab 顺序: 故事→角色卡→章节→工作流

---

## 待完成

### P0: 前端体验打磨

1. **章节 Tab 日期显示修复**
   - 文件: `frontend/src/components/chapters-list.tsx`
   - 问题: 显示 "Invalid Date"
   - 修复: 格式化 chapter_outline 中的时间字段

2. **工作流 Tab STAGES 升级为 8 阶段**
   - 文件: `frontend/src/components/workflow-waterfall.tsx:17-23`
   - 当前: 只显示 script/storyboard/image/audio/video (5阶段)
   - 目标: 显示 inspiration/story/chapter_outline/script/storyboard/image/audio/video (8阶段)
   - 同时更新 `STAGE_ORDER` 常量

3. **项目详情页 handleGenerate stageMap 升级**
   - 文件: `frontend/src/app/projects/[id]/page.tsx:66-68`
   - 当前: 只映射 script/storyboard/image/audio/video
   - 目标: 增加 inspiration/story/chapter_outline 映射

4. **工作流瀑布流显示章节信息**
   - 当前工作流是项目级，但每个章节/集应该独立
   - 需要支持按章节推进工作流的 UI

### P1: 前端功能

5. **流式生成展示**
   - 故事/剧本生成时显示实时打字效果
   - 需要: SSE streaming 后端 + 前端流式渲染

6. **视频预览播放器**
   - 工作流完成后可直接播放生成的 MP4

7. **首页 "灵感一键创作" 入口**
   - 首页增加灵感输入框 + "开始创作"按钮
   - 直接创建项目并跳转到故事向导

### P2: 后端完善

8. **MOCK_MODE 支持**
   - 开发环境无 API Key 时快速测试全流程

9. **错误恢复与重试**
   - 工作流某阶段失败后可重试

10. **多 Provider 容错链**
    - LLM: qwen → glm → kimi 自动切换
    - 图片: Wanx → SiliconFlow

### P3: 部署与运维

11. **docker-compose.prod.yml 去掉 version 警告**
    - 删除过时的 `version` 属性

12. **GitHub Actions CI/CD**
    - push novelforge → 自动部署到服务器

13. **服务器 docker 权限**
    - `sudo usermod -aG docker ubuntu` 避免每次 sudo

---

## 快速开发命令

```bash
# 前端开发
cd frontend && npm run dev

# 后端开发
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# 部署
cat <file> | ssh ubuntu@49.235.108.61 "cat > /tmp/f && sudo cp /tmp/f /opt/ops-video/<path>"
ssh ubuntu@49.235.108.61 "cd /opt/ops-video && sudo docker compose -f docker-compose.prod.yml up -d --build"
```
