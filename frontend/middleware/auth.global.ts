/** Protege todas las rutas salvo /login. */
export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie<string | null>('brickwise_token')
  if (!token.value && to.path !== '/login') {
    return navigateTo('/login')
  }
  if (token.value && to.path === '/login') {
    return navigateTo('/')
  }
})
