import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getMarcas } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
	const tipoRaw = params.tipo.toUpperCase();
	const tipo = tipoRaw as TipoVeiculo;

	if (!['MOTORCYCLE', 'CAR', 'TRUCK'].includes(tipo)) {
		throw error(400, 'Tipo inválido: ' + params.tipo);
	}

	try {
		const marcas = await getMarcas(tipo);
		return json({ marcas });
	} catch (e) {
		console.error('Error fetching marcas:', e);
		throw error(500, 'Erro ao carregar marcas');
	}
};
