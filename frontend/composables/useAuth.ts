/** Sesión de usuario: token JWT en cookie y llamadas a la API REST de auth. */

interface AuthUser {
  id: number
  email: string
  name: string
  teamId: number
  teamName: string
}

interface AuthResponse {
  accessToken: string
  tokenType: string
  user: {
    id: number
    email: string
    name: string
    team_id: number
    team_name: string
  }
}

export function useAuth() {
  const token = useCookie<string | null>('brickwise_token', {
    maxAge: 60 * 60 * 24 * 7,
    sameSite: 'lax',
  })

  function apiBase(): string {
    const config = useRuntimeConfig()
    return String(config.public.apiBase).replace(/\/graphql$/, '')
  }

  function mapUser(payload: AuthResponse['user']): AuthUser {
    return {
      id: payload.id,
      email: payload.email,
      name: payload.name,
      teamId: payload.team_id,
      teamName: payload.team_name,
    }
  }

  async function authenticate(
    path: 'login' | 'register',
    body: Record<string, unknown>,
  ): Promise<AuthUser> {
    const response = await $fetch<AuthResponse>(`${apiBase()}/auth/${path}`, {
      method: 'POST',
      body,
    })
    token.value = response.accessToken
    return mapUser(response.user)
  }

  function logout() {
    token.value = null
    return navigateTo('/login')
  }

  return { token, authenticate, logout }
}
