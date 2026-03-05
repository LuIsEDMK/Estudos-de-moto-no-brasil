import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getModelos } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
	const tipoRaw = params.tipo.toUpperCase();
	const tipo = tipoRaw as TipoVeiculo;
	const marca = decodeURIComponent(params.marca);

	if (!['MOTORCYCLE', 'CAR', 'TRUCK'].includes(tipo)) {
		throw error(400, 'Tipo inválido: ' + params.tipo);
	}

	if (!marca) {
		throw error(400, 'Marca é obrigatória');
	}

	try {
		const modelos = await getModelos(tipo, marca);
		return json({ modelos });
	} catch (e) {
		console.error('Error fetching modelos:', e);
		throw error(500, 'Erro ao carregar modelos');
	}
};
