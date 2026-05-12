/* ------------------------------------------------------------------ */
/* Story types — Phase 17.1.6                                          */
/* ------------------------------------------------------------------ */

export interface ChapterOutlineItem {
  chapter_number: number
  title: string
  summary: string
  estimated_duration: number  // in seconds
}

export interface Story {
  id: string
  project_id: string
  logline: string
  synopsis: string
  worldbuilding: string
  characters: string
  chapter_outline: ChapterOutlineItem[]
  created_at: string
  updated_at: string
}

export interface StoryCreate {
  logline?: string
  synopsis?: string
  worldbuilding?: string
  characters?: string
  chapter_outline?: ChapterOutlineItem[]
}

export interface StoryUpdate {
  logline?: string
  synopsis?: string
  worldbuilding?: string
  characters?: string
  chapter_outline?: ChapterOutlineItem[]
}

export interface InspirationRequest {
  inspiration: string
}

/* ------------------------------------------------------------------ */
/* Story Wizard types                                                   */
/* ------------------------------------------------------------------ */

export interface StoryWizardParams {
  inspiration: string
  genre: string
  tone: string
  target_length: string
  golden_finger: string
  protagonist: string
  relationship: string
  worldbuilding_hints: string
}

export const GENRE_OPTIONS = [
  { value: '东方玄幻', label: '东方玄幻', desc: '修仙 / 炼气 / 宗门 / 天道' },
  { value: '都市异能', label: '都市异能', desc: '现代背景 / 超能力 / 隐藏身份' },
  { value: '科幻星际', label: '科幻星际', desc: '机甲 / AI / 星际殖民' },
  { value: '古代言情', label: '古代言情', desc: '宫斗 / 江湖 / 权谋' },
  { value: '末世生存', label: '末世生存', desc: '丧尸 / 废土 / 异能觉醒' },
  { value: '游戏异界', label: '游戏异界', desc: '穿越游戏 / 系统流 / 等级打怪' },
]

export const TONE_OPTIONS = [
  { value: '热血激昂', label: '热血' },
  { value: '轻松搞笑', label: '轻松' },
  { value: '黑暗深沉', label: '黑暗' },
  { value: '悬疑惊悚', label: '悬疑' },
  { value: '温馨治愈', label: '治愈' },
]

export const GOLDEN_FINGER_OPTIONS = [
  { value: '上古传承', label: '上古传承', desc: '远古大能的功法或神器' },
  { value: '系统面板', label: '系统面板', desc: '游戏化数据面板辅助成长' },
  { value: '血脉觉醒', label: '血脉觉醒', desc: '隐藏血统逐步觉醒力量' },
  { value: '重生记忆', label: '重生记忆', desc: '带着前世记忆重新开始' },
  { value: '契约召唤', label: '契约召唤', desc: '召唤异界生物协助' },
  { value: '无金手指', label: '无金手指', desc: '纯靠智慧和努力' },
]

export const RELATIONSHIP_OPTIONS = [
  { value: '单女主', label: '单女主', desc: '专注一条感情线' },
  { value: '多女主', label: '多女主(后宫)', desc: '多条感情线并行' },
  { value: '无女主', label: '无女主(纯事业)', desc: '不涉及感情线' },
]

export const PROTAGONIST_OPTIONS = [
  { value: '杂役废柴逆袭', label: '杂役/废柴', desc: '出身低微，逆天改命' },
  { value: '世家天才陨落', label: '落难天才', desc: '曾经辉煌，跌落谷底' },
  { value: '平凡现代穿越', label: '穿越者', desc: '现代人穿越到异世界' },
  { value: '重生复仇', label: '重生者', desc: '带着记忆重新来过' },
  { value: '天命之子', label: '天命之子', desc: '生而不凡，注定成神' },
]

export const POWER_SYSTEM_OPTIONS = [
  { value: '练气修仙', label: '修仙体系', desc: '练气→筑基→金丹→元婴' },
  { value: '魔法斗气', label: '魔法斗气', desc: '魔法师/战士等级体系' },
  { value: '异能觉醒', label: '异能觉醒', desc: '现代超能力体系' },
  { value: '神话血脉', label: '神话血脉', desc: '神族/妖族血脉传承' },
]
