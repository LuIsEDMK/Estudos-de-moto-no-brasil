import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { analyzeVehicle } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const formData = await request.formData();
	const marca = formData.get('marca') as string;
	const modelo = formData.get('modelo') as string;
	const tipo = ((formData.get('tipo') as string) || 'MOTORCYCLE') as TipoVeiculo;
	const consultasFeitas = parseInt(formData.get('consultas_feitas') as string) || 0;

	if (!marca || !modelo) {
		throw error(400, 'Marca e modelo são obrigatórios');
	}

	// Check VIP status
	const vipToken = cookies.get('vip_token');
	const isVip = vipToken === '1';

	// Check free tier limit (based on client-provided count)
	if (!isVip && consultasFeitas >= 2) {
		throw error(403, 'Limite de consultas gratuitas atingido');
	}

	try {
		const result = await analyzeVehicle({ marca, modelo, tipo, isVip });
		return json({
			...result,
			consultas_restantes: isVip ? 999 : Math.max(0, 2 - consultasFeitas - 1)
		});
	} catch (e) {
		console.error('Error analyzing vehicle:', e);
		throw error(500, 'Erro ao analisar veículo');
	}
};
