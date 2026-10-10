'use client'

import { useEffect, useRef } from 'react'
import type { CSSProperties } from 'react'
import { useRouter } from 'next/navigation'

export function LandingExperience() {
  const pageRef = useRef<HTMLElement>(null)
  const router = useRouter()

  useEffect(() => {
    const page = pageRef.current
    if (!page) return

    const revealItems = page.querySelectorAll<HTMLElement>('[data-reveal]')
    const hero = page.querySelector<HTMLElement>('.hero')
    const heroSphere = page.querySelector<HTMLElement>('.hero__sphere')
    const backgroundVideo = page.querySelector<HTMLVideoElement>('.perspective__video')
    const canTiltHero =
      window.matchMedia('(hover: hover) and (pointer: fine)').matches &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let pointerFrame = 0
    let pointerPosition = { x: 0, y: 0 }
    const updatePointer = (event: PointerEvent) => {
      if (!hero || !heroSphere || !canTiltHero) return
      pointerPosition = {
        x: (event.clientX / window.innerWidth - 0.5) * 2,
        y: (event.clientY / window.innerHeight - 0.5) * 2,
      }
      if (pointerFrame) return

      pointerFrame = window.requestAnimationFrame(() => {
        const { x, y } = pointerPosition
        hero.style.setProperty('--glow-x', `${((x + 1) / 2) * 100}%`)
        hero.style.setProperty('--glow-y', `${((y + 1) / 2) * 100}%`)
        heroSphere.style.setProperty('--sphere-x', `${x * 16}px`)
        heroSphere.style.setProperty('--sphere-y', `${y * 12}px`)
        heroSphere.style.setProperty('--sphere-rotate-x', `${-y * 8}deg`)
        heroSphere.style.setProperty('--sphere-rotate-y', `${x * 10}deg`)
        pointerFrame = 0
      })
    }

    const resetPointer = () => {
      if (!hero || !heroSphere) return
      hero.style.removeProperty('--glow-x')
      hero.style.removeProperty('--glow-y')
      heroSphere.style.removeProperty('--sphere-x')
      heroSphere.style.removeProperty('--sphere-y')
      heroSphere.style.removeProperty('--sphere-rotate-x')
      heroSphere.style.removeProperty('--sphere-rotate-y')
    }

    if (hero && heroSphere && canTiltHero) {
      hero.addEventListener('pointermove', updatePointer)
      hero.addEventListener('pointerleave', resetPointer)
    }

    const startBackgroundVideo = () => {
      backgroundVideo?.play().catch((error: unknown) => {
        console.error('Section background video could not start playing.', error)
      })
    }
    backgroundVideo?.addEventListener('canplay', startBackgroundVideo, { once: true })
    if (backgroundVideo && backgroundVideo.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
      startBackgroundVideo()
    }

    let scrollObserver: IntersectionObserver | undefined
    if ('IntersectionObserver' in window && revealItems.length > 0) {
      page.classList.add('has-reveal')
      scrollObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible')
              scrollObserver?.unobserve(entry.target)
            }
          })
        },
        { threshold: 0.2, rootMargin: '-8% 0px -8% 0px' },
      )
      revealItems.forEach((item) => scrollObserver?.observe(item))
    } else {
      revealItems.forEach((item) => item.classList.add('is-visible'))
    }

    const futurePlanButton = page.querySelector<HTMLAnchorElement>('.future-plan__button')
    let coinRain: HTMLDivElement | undefined
    let animationTimeout = 0
    const coinAnimationDuration = 2800
    const startCoinRain = (event: MouseEvent) => {
      if (!futurePlanButton || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
      event.preventDefault()
      if (futurePlanButton.getAttribute('aria-disabled') === 'true') return

      const coinColumns = Math.min(80, Math.max(32, Math.ceil(window.innerWidth / 18)))
      const coinCount = coinColumns * 10
      let randomState = (performance.now() * 1000) >>> 0
      if (randomState === 0) randomState = 0x6d2b79f5
      const decorativeRandom = () => {
        randomState ^= randomState << 13
        randomState ^= randomState >>> 17
        randomState ^= randomState << 5
        return (randomState >>> 0) / 0x100000000
      }

      coinRain = document.createElement('div')
      coinRain.className = 'coin-rain'
      coinRain.setAttribute('aria-hidden', 'true')
      futurePlanButton.setAttribute('aria-disabled', 'true')

      for (let index = 0; index < coinCount; index += 1) {
        const coin = document.createElement('span')
        const size = 28 + decorativeRandom() * 22
        const column = index % coinColumns
        const screenPosition = ((column + decorativeRandom() * 0.9) / coinColumns) * 100
        coin.className = 'coin-rain__coin'
        coin.textContent = '₹'
        coin.style.setProperty('--coin-left', `${screenPosition}%`)
        coin.style.setProperty('--coin-size', `${size}px`)
        coin.style.setProperty('--coin-delay', `${decorativeRandom() * 100}ms`)
        coin.style.setProperty('--coin-duration', `${2100 + decorativeRandom() * 500}ms`)
        coin.style.setProperty('--coin-drift', `${decorativeRandom() * 140 - 70}px`)
        coinRain.append(coin)
      }
      document.body.append(coinRain)

      animationTimeout = window.setTimeout(() => {
        coinRain?.remove()
        coinRain = undefined
        futurePlanButton.removeAttribute('aria-disabled')
        router.push('/information')
      }, coinAnimationDuration)
    }

    futurePlanButton?.addEventListener('click', startCoinRain)

    return () => {
      scrollObserver?.disconnect()
      if (pointerFrame) window.cancelAnimationFrame(pointerFrame)
      if (hero && heroSphere && canTiltHero) {
        hero.removeEventListener('pointermove', updatePointer)
        hero.removeEventListener('pointerleave', resetPointer)
      }
      backgroundVideo?.removeEventListener('canplay', startBackgroundVideo)
      futurePlanButton?.removeEventListener('click', startCoinRain)
      window.clearTimeout(animationTimeout)
      coinRain?.remove()
      futurePlanButton?.removeAttribute('aria-disabled')
    }
  }, [router])

  const delayed = (milliseconds: number): CSSProperties =>
    ({ '--reveal-delay': `${milliseconds}ms` }) as CSSProperties

  return (
    <main className="landing-page" ref={pageRef}>
      <section className="hero" id="top" aria-labelledby="brand-name" data-scroll-section>
        <div className="hero__content">
          <a className="brand-mark" href="#top" aria-label="Future Fund home" data-reveal>
            <svg viewBox="0 0 64 64" role="img" aria-label="Future Fund mark">
              <circle cx="32" cy="32" r="30" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M40 19H27a8 8 0 0 0-8 8v19m0-14h17" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              <circle cx="45" cy="44" r="3" fill="currentColor" />
            </svg>
          </a>
          <h1 id="brand-name" data-reveal style={delayed(100)}>Future <span>Fund</span></h1>
          <p className="hero__quote" data-reveal style={delayed(200)}>
            “The best investment in your future is the one you begin today.”
          </p>
        </div>
        <div className="hero__sphere" aria-hidden="true">
          <span className="hero__sphere-core">
            <span className="hero__sphere-symbol">₹</span>
          </span>
          <span className="hero__sphere-orbit" />
          <span className="hero__sphere-orbit hero__sphere-orbit--tilted" />
        </div>
        <div className="hero__symbols" aria-hidden="true">
          <span className="hero__symbol hero__symbol--growth">↗</span>
          <span className="hero__symbol hero__symbol--percent">%</span>
          <span className="hero__symbol hero__symbol--dollar">$</span>
          <span className="hero__symbol hero__symbol--plus">+</span>
          <span className="hero__symbol hero__symbol--chart">⌁</span>
        </div>
        <a className="hero__scroll" href="#our-perspective" aria-label="Scroll to our perspective">
          <span />
        </a>
      </section>

      <section className="perspective" id="our-perspective" aria-labelledby="perspective-title" data-scroll-section>
        <video className="perspective__video" autoPlay muted loop playsInline preload="auto" aria-hidden="true" tabIndex={-1}>
          <source src="/preview_540p_crf22_higher_quality.mp4" type="video/mp4" />
        </video>
        <div className="perspective__backdrop" aria-hidden="true">
          <span className="perspective__glow" />
          <span className="perspective__grid" />
        </div>
        <div className="perspective__body">
          <p className="eyebrow" data-reveal>A perspective worth keeping</p>
          <h2 id="perspective-title" data-reveal style={delayed(100)}>
            Think beyond the next<br /><em>number.</em>
          </h2>
          <p className="perspective__copy" data-reveal style={delayed(200)}>
            Future Fund is your financial AI copilot, turning your goals and everyday money choices into clear, personal guidance for healthier finances.
          </p>
        </div>
        <div className="perspective__note" aria-hidden="true">A clearer view of what comes next</div>
      </section>

      <section className="future-plan" id="future-plan" aria-labelledby="future-plan-title" data-scroll-section>
        <div className="future-plan__content">
          <p className="eyebrow" data-reveal>Your next chapter</p>
          <h2 id="future-plan-title" data-reveal>
            Make your future<br /><em>a little more yours.</em>
          </h2>
          <p className="future-plan__copy" data-reveal style={delayed(100)}>
            Big goals begin with small, steady choices. Take the time to understand what matters to you, then move forward at your own pace.
          </p>
          <a className="future-plan__button" href="/information" data-reveal style={delayed(200)}>
            <span>Let’s see the future</span>
            <span className="button-arrow" aria-hidden="true">↗</span>
          </a>
        </div>
        <footer className="footer" data-reveal>
          <span className="footer__brand">FUTURE FUND</span>
          <span>Clarity for the road ahead.</span>
          <span>© {new Date().getFullYear()} Future Fund</span>
        </footer>
      </section>
    </main>
  )
}
