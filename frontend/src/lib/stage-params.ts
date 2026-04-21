/** Stage-specific parameter schemas for the parameter panel forms */

export type ParamType = 'text' | 'textarea' | 'number' | 'select'

export interface ParamField {
  key: string
  label: string
  type: ParamType
  placeholder?: string
  required?: boolean
  default?: string | number
  options?: { label: string; value: string | number }[]
  min?: number
  max?: number
  rows?: number
}

export const STAGE_PARAMS: Record<string, ParamField[]> = {
  script: [
    {
      key: 'prompt',
      label: '提示词',
      type: 'textarea',
      placeholder: '描述你想要的故事内容...',
      required: true,
      rows: 5,
    },
    {
      key: 'style',
      label: '风格',
      type: 'select',
      default: 'manga',
      options: [
        { label: '漫画', value: 'manga' },
        { label: '写实', value: 'realistic' },
        { label: '卡通', value: 'cartoon' },
        { label: '水彩', value: 'watercolor' },
      ],
    },
    {
      key: 'language',
      label: '语言',
      type: 'select',
      default: 'zh',
      options: [
        { label: '中文', value: 'zh' },
        { label: 'English', value: 'en' },
        { label: '日本語', value: 'ja' },
      ],
    },
  ],
  storyboard: [
    {
      key: 'prompt',
      label: '分镜描述',
      type: 'textarea',
      placeholder: '描述分镜要求或补充说明...',
      required: true,
      rows: 4,
    },
    {
      key: 'panel_count',
      label: '面板数量',
      type: 'number',
      default: 6,
      min: 1,
      max: 20,
    },
    {
      key: 'style',
      label: '风格',
      type: 'select',
      default: 'manga',
      options: [
        { label: '漫画', value: 'manga' },
        { label: '写实', value: 'realistic' },
        { label: '卡通', value: 'cartoon' },
      ],
    },
  ],
  image: [
    {
      key: 'prompt',
      label: '图片描述',
      type: 'textarea',
      placeholder: '描述你想要的图片画面...',
      required: true,
      rows: 4,
    },
    {
      key: 'resolution',
      label: '分辨率',
      type: 'select',
      default: '512x768',
      options: [
        { label: '512×768', value: '512x768' },
        { label: '768x512', value: '768x512' },
        { label: '1024×1024', value: '1024x1024' },
      ],
    },
    {
      key: 'style',
      label: '风格',
      type: 'select',
      default: 'manga',
      options: [
        { label: '漫画', value: 'manga' },
        { label: '写实', value: 'realistic' },
        { label: '水彩', value: 'watercolor' },
      ],
    },
  ],
  audio: [
    {
      key: 'voice',
      label: '声音',
      type: 'select',
      default: 'zh-CN-XiaoxiaoNeural',
      options: [
        { label: '晓晓 (女)', value: 'zh-CN-XiaoxiaoNeural' },
        { label: '云健 (男)', value: 'zh-CN-YunjianNeural' },
        { label: '云希 (男)', value: 'zh-CN-YunxiNeural' },
        { label: '晓艺 (女)', value: 'zh-CN-XiaoyiNeural' },
      ],
    },
    {
      key: 'speed',
      label: '语速',
      type: 'number',
      default: 1.0,
      min: 0.5,
      max: 2.0,
    },
    {
      key: 'bgm_style',
      label: '背景音乐',
      type: 'select',
      default: 'ambient',
      options: [
        { label: '环境音', value: 'ambient' },
        { label: '戏剧', value: 'dramatic' },
        { label: '欢快', value: 'cheerful' },
        { label: '悲伤', value: 'sad' },
        { label: '无', value: 'none' },
      ],
    },
  ],
  video: [
    {
      key: 'fps',
      label: '帧率',
      type: 'number',
      default: 24,
      min: 12,
      max: 60,
    },
    {
      key: 'resolution',
      label: '分辨率',
      type: 'select',
      default: '720p',
      options: [
        { label: '480p', value: '480p' },
        { label: '720p', value: '720p' },
        { label: '1080p', value: '1080p' },
      ],
    },
    {
      key: 'transition',
      label: '转场效果',
      type: 'select',
      default: 'fade',
      options: [
        { label: '淡入淡出', value: 'fade' },
        { label: '滑动', value: 'slide' },
        { label: '缩放', value: 'zoom' },
        { label: '无', value: 'none' },
      ],
    },
  ],
}
