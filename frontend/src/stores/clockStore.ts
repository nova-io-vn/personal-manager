import { useEffect } from 'react'
import { create } from 'zustand'

interface ClockState {
  now: Date
}

const clockStore = create<ClockState>(() => ({ now: new Date() }))
let timer: ReturnType<typeof setInterval> | undefined
let consumers = 0

/** A single shared 30-second clock for Calendar and Dashboard time-derived UI. */
export function useAppClock(): Date {
  const now = clockStore((state) => state.now)

  useEffect(() => {
    consumers += 1
    if (!timer) {
      clockStore.setState({ now: new Date() })
      timer = setInterval(() => clockStore.setState({ now: new Date() }), 30_000)
    }
    return () => {
      consumers -= 1
      if (consumers <= 0 && timer) {
        clearInterval(timer)
        timer = undefined
        consumers = 0
      }
    }
  }, [])

  return now
}
