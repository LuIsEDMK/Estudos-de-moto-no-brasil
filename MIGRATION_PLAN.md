# Migration Plan: FastAPI → SvelteKit (Svelte 5)

## Project Structure

```
motoexpert-ai/
├── src/
│   ├── app.html                 # HTML template
│   ├── app.d.ts                 # Type definitions
│   ├── lib/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── sidebar/
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   ├── LoginSection.svelte
│   │   │   │   ├── CategorySelector.svelte
│   │   │   │   └── VehicleSearch.svelte
│   │   │   ├── charts/
│   │   │   │   ├── DepreciationChart.svelte
│   │   │   │   └── ComparisonChart.svelte
│   │   │   ├── ui/
│   │   │   │   ├── Button.svelte
│   │   │   │   ├── Card.svelte
│   │   │   │   ├── Badge.svelte
│   │   │   │   └── Select.svelte
│   │   │   └── reports/
│   │   │       ├── RankingTable.svelte
│   │   │       └── MotoDetail.svelte
│   │   ├── server/              # Server-side utilities
│   │   │   ├── auth.ts          # Google auth validation
│   │   │   ├── data.ts          # Data loading & processing
│   │   │   └── sheets.ts        # Google Sheets integration
│   │   ├── stores/              # Svelte 5 runes-based state
│   │   │   ├── auth.svelte.ts   # Auth state
│   │   │   ├── vehicle.svelte.ts # Vehicle selection state
│   │   │   └── ui.svelte.ts     # UI state
│   │   └── types/               # TypeScript types
│   │       └── index.ts
│   ├── routes/                  # Page routes
│   │   ├── +layout.svelte       # Root layout with sidebar
│   │   ├── +layout.ts           # Root layout load
│   │   ├── +page.svelte         # Redirect to /analise
│   │   ├── analise/
│   │   │   ├── +page.svelte     # Desvalorização main page
│   │   │   ├── +page.server.ts  # Load brands data
│   │   │   └── ResultCard.svelte # Scoped: analysis results
│   │   ├── relatorios/
│   │   │   ├── +page.svelte     # VIP Reports page
│   │   │   ├── +page.server.ts  # Load rankings (VIP only)
│   │   │   ├── RecentesSection.svelte
│   │   │   ├── BaratasSection.svelte
│   │   │   └── BombasSection.svelte
│   │   ├── comparar/
│   │   │   ├── +page.svelte     # Tira-Teima comparison
│   │   │   ├── +page.server.ts  # Load data for comparison
│   │   │   ├── VehiclePicker.svelte
│   │   │   └── VerdictCard.svelte
│   │   ├── tutorial/
│   │   │   ├── +page.svelte     # Como Usar tutorial
│   │   │   ├── StepCard.svelte
│   │   │   ├── ExampleChart.svelte
│   │   │   └── FAQ.svelte
│   │   ├── assinar/
│   │   │   ├── +page.svelte     # Pricing page
│   │   │   ├── PricingCard.svelte
│   │   │   └── FeatureList.svelte
│   │   └── api/                 # API endpoints (internal)
│   │       ├── auth/
│   │       │   ├── login/+server.ts      # Google login
│   │       │   └── logout/+server.ts     # Logout
│   │       ├── marcas/
│   │       │   └── [tipo]/+server.ts     # GET brands by type
│   │       ├── modelos/
│   │       │   └── [tipo]/[marca]/+server.ts  # GET models
│   │       ├── analyze/+server.ts        # POST analyze
│   │       ├── compare/+server.ts        # POST compare
│   │       └── vip/
│   │           └── reports/+server.ts    # GET VIP reports
│   └── params/                  # Param matchers (if needed)
├── static/
│   ├── css/                     # Global styles only
│   │   └── base.css
│   └── favicon.png
├── tests/
├── package.json
├── svelte.config.js
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## Route Hierarchy

```
+layout.svelte (persistent sidebar + header)
├── / (redirects to /analise)
├── /analise (Desvalorização)
│   └── Server loads: brands for selected type
├── /relatorios (VIP Reports)
│   └── Server loads: rankings (protected)
├── /comparar (Tira-Teima)
│   └── Server loads: nothing (client-side)
├── /tutorial (Como Usar)
│   └── Server loads: nothing (static content)
└── /assinar (Pricing)
    └── Server loads: nothing (static content)
```

## Component Breakdown with Scoped Styles

### 1. Sidebar Components (`lib/components/sidebar/`)

**Sidebar.svelte** (container)

```svelte
<aside class="sidebar">
	<LoginSection />
	<CategorySelector />
	<VehicleSearch />
</aside>

<style>
	.sidebar {
		@apply flex w-full flex-shrink-0 flex-col gap-4 lg:w-64 xl:w-72;
	}
</style>
```

**LoginSection.svelte** (scoped)

```svelte
<script lang="ts">
	import { auth } from '$lib/stores/auth.svelte';

	let credential = $state('');
	let error = $state<string | null>(null);
</script>

<div class="login-panel">
	<h2 class="title">
		<svg class="icon" viewBox="0 0 24 24">...</svg>
		Acesso VIP
	</h2>

	{#if auth.usuarioVip}
		<div class="success-message">👑 Acesso VIP liberado!</div>
		<button class="logout-btn" onclick={auth.logout}>Sair</button>
	{:else}
		<div id="g_id_onload" data-callback="handleCredentialResponse">...</div>
		<div class="g_id_signin">...</div>
	{/if}
</div>

<style>
	.login-panel {
		@apply panel p-4;
	}
	.title {
		@apply mb-3 flex items-center gap-2 text-sm font-bold;
		color: rgb(var(--color-content-muted));
	}
	.icon {
		@apply h-4 w-4 text-amber-500;
	}
	.success-message {
		@apply alert alert-success py-2 text-xs;
	}
	.logout-btn {
		@apply mt-2 w-full text-xs text-rose-500 hover:text-rose-600;
	}
</style>
```

**CategorySelector.svelte** (scoped)

```svelte
<script lang="ts">
	import { vehicle } from '$lib/stores/vehicle.svelte';
</script>

<div class="category-panel">
	<h3 class="title">Categoria</h3>
	<div class="grid">
		{#each ['MOTORCYCLE', 'CAR', 'TRUCK'] as tipo}
			<button
				class="category-btn"
				class:active={vehicle.tipo === tipo}
				onclick={() => vehicle.setTipo(tipo)}
			>
				{tipo === 'MOTORCYCLE' ? '🏍️' : tipo === 'CAR' ? '🚗' : '🚛'}
				{tipo === 'MOTORCYCLE' ? 'Motos' : tipo === 'CAR' ? 'Carros' : 'Caminhões'}
			</button>
		{/each}
	</div>
</div>

<style>
	.category-panel {
		@apply panel p-4;
	}
	.title {
		@apply mb-3 text-sm font-bold;
		color: rgb(var(--color-content-muted));
	}
	.grid {
		@apply grid grid-cols-3 gap-2;
	}
	.category-btn {
		@apply btn-category;
	}
	.category-btn.active {
		@apply btn-category-active;
	}
</style>
```

### 2. Chart Components (`lib/components/charts/`)

**DepreciationChart.svelte**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import type { ChartData } from '$lib/types';

	interface Props {
		data: ChartData;
		isVip: boolean;
	}

	let { data, isVip }: Props = $props();
	let chartEl = $state<HTMLDivElement>();

	onMount(() => {
		// Plotly initialization
		const isDark = document.documentElement.classList.contains('dark');
		// ... chart config
	});
</script>

<div class="chart-wrapper" bind:this={chartEl}></div>

<style>
	.chart-wrapper {
		@apply h-80 w-full;
	}
</style>
```

### 3. Page-Specific Components (co-located)

Each page can have its own components that aren't shared:

```
routes/analise/
├── +page.svelte
├── +page.server.ts
├── ResultCard.svelte      # Only used here
├── PriceDisplay.svelte    # Only used here
└── TableLocked.svelte     # Only used here
```

## Svelte 5 Runes-Based State Management

### Auth Store (`lib/stores/auth.svelte.ts`)

```typescript
import type { User } from '$lib/types';

function createAuthStore() {
	let usuarioVip = $state(false);
	let user = $state<User | null>(null);
	let loading = $state(false);

	return {
		get usuarioVip() {
			return usuarioVip;
		},
		get user() {
			return user;
		},
		get loading() {
			return loading;
		},

		async loginWithGoogle(credential: string) {
			loading = true;
			const res = await fetch('/api/auth/login', {
				method: 'POST',
				body: JSON.stringify({ credential })
			});
			const data = await res.json();
			usuarioVip = data.vip;
			loading = false;
		},

		async logout() {
			await fetch('/api/auth/logout', { method: 'POST' });
			usuarioVip = false;
			user = null;
		}
	};
}

export const auth = createAuthStore();
```

### Vehicle Store (`lib/stores/vehicle.svelte.ts`)

```typescript
import type { Marca, Modelo, TipoVeiculo } from '$lib/types';

function createVehicleStore() {
	let tipo = $state<TipoVeiculo>('MOTORCYCLE');
	let marca = $state<string>('');
	let modelo = $state<string>('');
	let marcas = $state<Marca[]>([]);
	let modelos = $state<Modelo[]>([]);

	// Derived values
	let canAnalyze = $derived(marca && modelo);

	return {
		get tipo() {
			return tipo;
		},
		get marca() {
			return marca;
		},
		get modelo() {
			return modelo;
		},
		get marcas() {
			return marcas;
		},
		get modelos() {
			return modelos;
		},
		get canAnalyze() {
			return canAnalyze;
		},

		setTipo(newTipo: TipoVeiculo) {
			tipo = newTipo;
			marca = '';
			modelo = '';
			// Load brands for new type
		},

		setMarca(newMarca: string) {
			marca = newMarca;
			modelo = '';
			// Load models for brand
		}
	};
}

export const vehicle = createVehicleStore();
```

## API Migration (SvelteKit Server Routes)

Current FastAPI endpoints → SvelteKit:

| FastAPI                           | SvelteKit                                      | Method |
| --------------------------------- | ---------------------------------------------- | ------ |
| `GET /`                           | `routes/+page.svelte`                          | Render |
| `POST /api/login`                 | `routes/api/auth/login/+server.ts`             | POST   |
| `POST /api/logout`                | `routes/api/auth/logout/+server.ts`            | POST   |
| `POST /api/analyze`               | `routes/api/analyze/+server.ts`                | POST   |
| `GET /api/vip/reports`            | `routes/api/vip/reports/+server.ts`            | GET    |
| `POST /api/compare`               | `routes/api/compare/+server.ts`                | POST   |
| `GET /api/marcas/{tipo}`          | `routes/api/marcas/[tipo]/+server.ts`          | GET    |
| `GET /api/modelos/{tipo}/{marca}` | `routes/api/modelos/[tipo]/[marca]/+server.ts` | GET    |

### Example: analyze/+server.ts

```typescript
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { analyzeVehicle } from '$lib/server/data';

export const POST: RequestHandler = async ({ request, locals }) => {
	const formData = await request.formData();
	const marca = formData.get('marca') as string;
	const modelo = formData.get('modelo') as string;
	const tipo = formData.get('tipo') as string;

	const isVip = locals.user?.vip ?? false;

	const result = await analyzeVehicle({ marca, modelo, tipo, isVip });

	return json(result);
};
```

## Layout Structure

```svelte
<!-- +layout.svelte -->
<script lang="ts">
	import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
	import Header from '$lib/components/layout/Header.svelte';
	import '../app.css';
</script>

<div class="app">
	<Header />

	<div class="container">
		<Sidebar />

		<main class="main-content">
			<slot />
		</main>
	</div>
</div>

<style>
	.app {
		@apply min-h-screen;
	}
	.container {
		@apply mx-auto max-w-7xl px-4 py-6 sm:px-6;
		@apply flex flex-col gap-6 lg:flex-row;
	}
	.main-content {
		@apply min-w-0 flex-1;
	}
</style>
```

## Global Styles (minimal)

Only put in `app.css`:

- CSS variables for theming
- Utility classes used everywhere
- Tailwind base imports

Component-specific styles stay in `<style>` blocks.

## Task Checklist

### Phase 1: Setup

- [ ] Initialize SvelteKit project with `npm create svelte@latest motoexpert-ai`
- [ ] Configure Tailwind CSS
- [ ] Setup TypeScript strict mode
- [ ] Copy static assets (CSS, images)
- [ ] Install dependencies (plotly, etc.)

### Phase 2: Core Infrastructure

- [ ] Create type definitions
- [ ] Setup Svelte 5 runes stores (auth, vehicle)
- [ ] Create server-side data utilities
- [ ] Migrate Google Sheets auth logic

### Phase 3: Layout & Navigation

- [ ] Create +layout.svelte with sidebar
- [ ] Create Sidebar component with children
- [ ] Create Header component
- [ ] Implement navigation between pages

### Phase 4: Pages

- [ ] /analise page (main analysis tool)
- [ ] /relatorios page (VIP reports)
- [ ] /comparar page (comparison tool)
- [ ] /tutorial page (how-to guide)
- [ ] /assinar page (pricing)

### Phase 5: API Routes

- [ ] /api/auth/login
- [ ] /api/auth/logout
- [ ] /api/marcas/[tipo]
- [ ] /api/modelos/[tipo]/[marca]
- [ ] /api/analyze
- [ ] /api/compare
- [ ] /api/vip/reports

### Phase 6: Components

- [ ] Chart components (Depreciation, Comparison)
- [ ] UI components (Button, Card, Select, Badge)
- [ ] Report table components
- [ ] Vehicle picker components

### Phase 7: Polish

- [ ] Dark mode support
- [ ] Loading states
- [ ] Error handling
- [ ] Responsive design verification
- [ ] VIP access restrictions

## Migration Strategy

1. **Start with layout + sidebar** - Get navigation working first
2. **Do /analise first** - It's the most complex page, will establish patterns
3. **Migrate data layer** - Port CSV loading and calculations
4. **Add remaining pages** - They share patterns from /analise
5. **Test auth flow** - Ensure VIP access works

## Notes on Svelte 5

- Use `$state()` for reactive variables
- Use `$derived()` for computed values
- Use `$effect()` for side effects (like chart rendering)
- Use `$props()` for component props (with destructuring)
- Event handlers are just functions now (no `on:` prefix)
- Snippets for reusable template chunks

## File Size Targets

Keep components small:

- Components: < 200 lines ideally, < 400 max
- Page files: < 300 lines (split into sub-components)
- Server routes: < 150 lines (extract logic to lib/server/)
