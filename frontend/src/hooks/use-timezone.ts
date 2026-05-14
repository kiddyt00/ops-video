'use client'

import { useState, useEffect } from 'react'

export interface TimezoneInfo {
  timezone: string
  offset: string
  offsetMinutes: number
}

function getTimezoneOffsetMinutes(): number {
  return -new Date().getTimezoneOffset()
}

function formatOffset(minutes: number): string {
  const sign = minutes >= 0 ? '+' : '-'
  const abs = Math.abs(minutes)
  const hours = Math.floor(abs / 60)
  const mins = abs % 60
  return `UTC${sign}${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

export function useTimezone(): TimezoneInfo {
  const [info, setInfo] = useState<TimezoneInfo>(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
    const offsetMinutes = getTimezoneOffsetMinutes()
    return {
      timezone: tz,
      offset: formatOffset(offsetMinutes),
      offsetMinutes,
    }
  })

  useEffect(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
    const offsetMinutes = getTimezoneOffsetMinutes()
    setInfo({
      timezone: tz,
      offset: formatOffset(offsetMinutes),
      offsetMinutes,
    })
  }, [])

  return info
}
