/** Ejecuta una operación GraphQL contra la API de Brickwise (con sesión). */
export async function gql<T>(
  query: string,
  variables: Record<string, unknown> = {},
): Promise<T> {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('brickwise_token')
  const response = await $fetch<T>(config.public.apiBase, {
    method: 'POST',
    body: { query, variables },
    headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
  })
  return response
}

/** Base REST de la API (sin el sufijo /graphql). */
export function apiRoot(): string {
  const config = useRuntimeConfig()
  return String(config.public.apiBase).replace(/\/graphql$/, '')
}
