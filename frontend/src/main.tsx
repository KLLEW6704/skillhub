import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { Providers } from './app/providers'
import { router } from './app/router'
import './styles/index.css'
import './styles/workspace.css'
import './styles/requester.css'
import './styles/evidence.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers><RouterProvider router={router} /></Providers>
  </StrictMode>,
)
