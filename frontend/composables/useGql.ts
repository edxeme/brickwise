/** Ejecuta una operación GraphQL contra la API de Brickwise. */
export async function gql<T>(
  query: string,
  variables: Record<string, unknown> = {},
): Promise<T> {
  const config = useRuntimeConfig()
  return await $fetch<T>(config.public.apiBase, {
    method: 'POST',
    body: { query, variables },
  })
}
