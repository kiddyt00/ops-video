import { type TaskStage } from '@/types/task'
import { AppHeader } from '@/components/app-header'
import { StageSidebar } from '@/components/stage-sidebar'
import { ParameterPanel } from '@/components/parameter-panel'

interface ThreePanelLayoutProps {
  header?: {
    projectName?: string
    workflowStatus?: {
      current_stage: string | null
      stages: { stage: string; status: string }[]
    }
  }
  sidebar?: {
    currentStage?: TaskStage | null
    completedStages?: TaskStage[]
    onSelectStage?: (stage: TaskStage) => void
  }
  panel?: {
    stage?: TaskStage | null
    parameters?: Record<string, unknown>
    onGenerate?: (params: Record<string, unknown>) => void
    onAdvance?: () => void
    onRollback?: () => void
    canGenerate?: boolean
    canAdvance?: boolean
  }
  children: React.ReactNode
}

export function ThreePanelLayout({ header, sidebar, panel, children }: ThreePanelLayoutProps) {
  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <AppHeader projectName={header?.projectName} workflowStatus={header?.workflowStatus} />
      <div className="flex flex-1 overflow-hidden">
        {sidebar && (
          <StageSidebar
            currentStage={sidebar.currentStage}
            completedStages={sidebar.completedStages}
            onSelectStage={sidebar.onSelectStage}
          />
        )}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
        {panel && (
          <ParameterPanel
            stage={panel.stage}
            parameters={panel.parameters}
            onGenerate={panel.onGenerate}
            onAdvance={panel.onAdvance}
            onRollback={panel.onRollback}
            canGenerate={panel.canGenerate}
            canAdvance={panel.canAdvance}
          />
        )}
      </div>
    </div>
  )
}
