import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { recomendarVeiculos } from '$lib/server/recomendador';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json();
		const { orcamento, tipoPreferencia, anoMinimo, anoMaximo } = body;

		if (!orcamento || orcamento <= 0) {
			throw error(400, 'Orçamento inválido');
		}

		const recomendacoes = await recomendarVeiculos({
			orcamento,
			tipoPreferencia: tipoPreferencia || 'TODOS',
			anoMinimo: anoMinimo || 1990,
			anoMaximo: anoMaximo || new Date().getFullYear()
		});

		return json({
			sucesso: true,
			orcamento,
			recomendacoes
		});
	} catch (e) {
		console.error('Erro na recomendação:', e);
		throw error(500, 'Erro ao gerar recomendações');
	}
};
