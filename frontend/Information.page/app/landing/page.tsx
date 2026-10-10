import type { Metadata } from 'next'
import { LandingExperience } from './landing-experience'
import './landing.css'

export const metadata: Metadata = {
  title: 'Future Fund — Make tomorrow matter',
  description: 'Future Fund helps you make thoughtful financial decisions for the life ahead.',
}

export default function LandingPage() {
  return <LandingExperience />
}
