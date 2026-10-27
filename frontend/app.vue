<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <NuxtLink to="/" class="text-lg font-semibold tracking-tight">
          🧱 Brickwise
        </NuxtLink>
        <div class="flex gap-6 text-sm text-slate-600">
          <NuxtLink to="/" class="hover:text-slate-900">Proyectos</NuxtLink>
          <NuxtLink to="/normativa" class="hover:text-slate-900">Normativa</NuxtLink>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-6 py-8">
      <NuxtPage />
    </main>
  </div>
</template>
