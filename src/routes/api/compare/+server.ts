import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { compareVehicles } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const formData = await request.formData();
	const marcaA = formData.get('marca_a') as string;
	const modeloA = formData.get('modelo_a') as string;
	const marcaB = formData.get('marca_b') as string;
	const modeloB = formData.get('modelo_b') as string;
	const tipo = ((formData.get('tipo') as string) || 'MOTORCYCLE') as TipoVeiculo;

	if (!marcaA || !modeloA || !marcaB || !modeloB) {
		throw error(400, 'Todos os campos são obrigatórios');
	}

	// Check VIP status
	const isVip = cookies.get('vip_token') === '1';
	if (!isVip) {
		throw error(403, 'Comparador exclusivo para VIP');
	}

	try {
		const result = await compareVehicles({ marcaA, modeloA, marcaB, modeloB, tipo });
		return json(result);
	} catch (e) {
		console.error('Error comparing vehicles:', e);
		throw error(500, 'Erro ao comparar veículos');
	}
};
