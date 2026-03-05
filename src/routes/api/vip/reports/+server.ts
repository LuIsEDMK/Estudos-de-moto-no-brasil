import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { generateVipReports } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const GET: RequestHandler = async ({ url, cookies }) => {
	const tipo = (url.searchParams.get('tipo') || 'MOTORCYCLE') as TipoVeiculo;
	const isVip = cookies.get('vip_token') === '1';

	if (!isVip) {
		// Return preview data for non-VIP
		return json({
			vip: false,
			degustacao: [
				{
					ranking: '1º',
					marca: 'H****',
					modelo: 'C* *** *****',
					preco: 'R$ **.***,**',
					perda: '🔒 VIP'
				},
				{
					ranking: '2º',
					marca: 'Y*****',
					modelo: 'F***** ***',
					preco: 'R$ **.***,**',
					perda: '🔒 VIP'
				},
				{ ranking: '3º', marca: 'B**', modelo: 'G *** *', preco: 'R$ **.***,**', perda: '🔒 VIP' }
			]
		});
	}

	try {
		const reports = await generateVipReports(tipo);

		// Recentes: 2024+, sorted by lowest depreciation
		const recentes = reports
			.filter((r) => r.ano_modelo_novo >= 2024)
			.sort((a, b) => a.queda_anual_media - b.queda_anual_media)
			.slice(0, 10);

		// Baratas: <= 15000, >= 2018, sorted by lowest depreciation
		const baratas = reports
			.filter((r) => r.preco_limpo_novo <= 15000 && r.ano_modelo_novo >= 2018)
			.sort((a, b) => a.queda_anual_media - b.queda_anual_media)
			.slice(0, 10);

		// Bombas: 2022+, sorted by highest depreciation (worst first)
		const bombas = reports
			.filter((r) => r.ano_modelo_novo >= 2022)
			.sort((a, b) => b.queda_anual_media - a.queda_anual_media)
			.slice(0, 10);

		return json({
			vip: true,
			recentes,
			baratas,
			bombas
		});
	} catch (e) {
		console.error('Error generating reports:', e);
		return json({ vip: false, degustacao: [] });
	}
};
