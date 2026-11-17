import { Navigate } from 'react-router-dom'
import { ErrorState, LoadingState } from '../../components/common/Feedback'
import AboutSection from '../../components/landing/AboutSection'
import ContactSection from '../../components/landing/ContactSection'
import { HeroSection, PhotoStrip } from '../../components/landing/HeroSection'
import LandingFooter from '../../components/landing/LandingFooter'
import LandingHeader from '../../components/landing/LandingHeader'
import ServicesSection from '../../components/landing/ServicesSection'
import { useApiQuery } from '../../hooks/useApiQuery'
import { landingService } from '../../services'
import { isStandalone } from '../../utils/pwa'
import './landing.css'

/**
 * The public DLL Library website. Everything on it is read from the backend
 * (edited by the Admin in Library Settings); the hours are the same ones that
 * govern reservations.
 *
 * The installed app never shows this page: it goes straight to sign-in (and
 * from there to the dashboard when already signed in).
 */
export default function LandingPage() {
  const standalone = isStandalone()
  const query = useApiQuery(landingService.public, [], { enabled: !standalone })

  if (standalone) return <Navigate to="/login" replace />

  return (
    <div className="landing">
      <LandingHeader />
      <main>
        {query.data ? (
          <>
            <HeroSection data={query.data} />
            <PhotoStrip photos={query.data.photos} />
            <ServicesSection services={query.data.services} />
            <AboutSection data={query.data} />
            <ContactSection data={query.data} />
          </>
        ) : (
          <div className="landing-container landing-loading">
            {query.error
              ? <ErrorState error={query.error} onRetry={query.refetch} />
              : <LoadingState label="Loading DLL Library..." />}
          </div>
        )}
      </main>
      {query.data && <LandingFooter profile={query.data.profile} />}
    </div>
  )
}
