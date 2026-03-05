import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { analyzeVehicle } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const formData = await request.formData();
	const marca = formData.get('marca') as string;
	const modelo = formData.get('modelo') as string;
	const tipo = ((formData.get('tipo') as string) || 'MOTORCYCLE') as TipoVeiculo;
	if (!marca || !modelo) {
		throw error(400, 'Marca e modelo são obrigatórios');
	}

	// VIP status vindo do cliente (para testes locais)
	// Em produção, isso deve ser verificado no servidor via cookie/JWT
	const isVip = formData.get('isVip') === 'true';

	try {
		const result = await analyzeVehicle({ marca, modelo, tipo, isVip });
		return json(result);
	} catch (e) {
		console.error('Error analyzing vehicle:', e);
		throw error(500, 'Erro ao analisar veículo');
	}
};
