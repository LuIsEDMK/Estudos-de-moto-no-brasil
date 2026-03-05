import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { analyzeVehicle } from '$lib/server/data';
import type { TipoVeiculo } from '$lib/types';

export const POST: RequestHandler = async ({ request, cookies }) => {
    // Comparador disponível para todos (sem verificação VIP)
    console.log('[API Compare] Requisição recebida');

    try {
        const body = await request.json();
        const { vehicleA, vehicleB } = body;
        
        if (!vehicleA?.marca || !vehicleA?.modelo || !vehicleB?.marca || !vehicleB?.modelo) {
            throw error(400, 'Dados incompletos. Forneça marca e modelo para ambos os veículos.');
        }

        const tipoA = (vehicleA.tipo || 'MOTORCYCLE') as TipoVeiculo;
        const tipoB = (vehicleB.tipo || 'MOTORCYCLE') as TipoVeiculo;

        // Analyze both vehicles
        const [analysisA, analysisB] = await Promise.all([
            analyzeVehicle({ 
                marca: vehicleA.marca, 
                modelo: vehicleA.modelo, 
                tipo: tipoA, 
                isVip: true 
            }),
            analyzeVehicle({ 
                marca: vehicleB.marca, 
                modelo: vehicleB.modelo, 
                tipo: tipoB, 
                isVip: true 
            })
        ]);

        if ('error' in analysisA || 'error' in analysisB) {
            throw error(404, 'Não foi possível analisar um ou ambos os veículos');
        }

        // Extract price evolution data
        const priceEvolutionA = analysisA.grafico_price_evolution.map(p => ({ year: p.year, price: p.value }));
        const priceEvolutionB = analysisB.grafico_price_evolution.map(p => ({ year: p.year, price: p.value }));
        
        // Calculate current prices (most recent year)
        const currentPriceA = priceEvolutionA[0]?.price || 0;
        const currentPriceB = priceEvolutionB[0]?.price || 0;
        
        const initialPriceA = priceEvolutionA[priceEvolutionA.length - 1]?.price || currentPriceA;
        const initialPriceB = priceEvolutionB[priceEvolutionB.length - 1]?.price || currentPriceB;
        
        // Calculate total depreciation
        const totalDepA = initialPriceA > 0 ? ((initialPriceA - currentPriceA) / initialPriceA) * 100 : 0;
        const totalDepB = initialPriceB > 0 ? ((initialPriceB - currentPriceB) / initialPriceB) * 100 : 0;

        // Average yearly drop from analysis
        const yearlyDropValuesA = analysisA.grafico_yearly_drop.map(d => d.drop);
        const yearlyDropValuesB = analysisB.grafico_yearly_drop.map(d => d.drop);
        const avgYearlyDropA = yearlyDropValuesA.length > 0 
            ? yearlyDropValuesA.reduce((a, b) => a + b, 0) / yearlyDropValuesA.length 
            : 0;
        const avgYearlyDropB = yearlyDropValuesB.length > 0 
            ? yearlyDropValuesB.reduce((a, b) => a + b, 0) / yearlyDropValuesB.length 
            : 0;

        // Year ranges
        const yearsA = priceEvolutionA.map(p => p.year);
        const yearsB = priceEvolutionB.map(p => p.year);
        const yearRangeA = yearsA.length > 0 ? `${Math.min(...yearsA)}-${Math.max(...yearsA)}` : 'N/A';
        const yearRangeB = yearsB.length > 0 ? `${Math.min(...yearsB)}-${Math.max(...yearsB)}` : 'N/A';

        // Scoring: Price (40%) + Retention (60%)
        const priceScoreA = currentPriceB > 0 ? Math.min(100, (currentPriceB / currentPriceA) * 100) : 50;
        const priceScoreB = currentPriceA > 0 ? Math.min(100, (currentPriceA / currentPriceB) * 100) : 50;
        
        const retentionScoreA = totalDepA < totalDepB ? 100 : Math.max(0, 100 - (totalDepA - totalDepB) * 5);
        const retentionScoreB = totalDepB < totalDepA ? 100 : Math.max(0, 100 - (totalDepB - totalDepA) * 5);
        
        const scoreA = priceScoreA * 0.4 + retentionScoreA * 0.6;
        const scoreB = priceScoreB * 0.4 + retentionScoreB * 0.6;

        // Determine winner
        let winner: 'A' | 'B' | 'tie';
        if (Math.abs(scoreA - scoreB) < 5) {
            winner = 'tie';
        } else if (scoreA > scoreB) {
            winner = 'A';
        } else {
            winner = 'B';
        }

        // Build comparison table
        const allYears = [...new Set([...yearsA, ...yearsB])].sort((a, b) => b - a);

        const comparisonTable = allYears.map(year => {
            const priceA = priceEvolutionA.find(p => p.year === year)?.price || 0;
            const priceB = priceEvolutionB.find(p => p.year === year)?.price || 0;
            return {
                year,
                vehicleAPrice: priceA,
                vehicleBPrice: priceB,
                difference: priceA - priceB
            };
        });

        // Generate analysis text
        const priceDiff = Math.abs(currentPriceA - currentPriceB);
        const cheaper = currentPriceA < currentPriceB ? 'A' : 'B';
        const betterRetention = totalDepA < totalDepB ? 'A' : totalDepB < totalDepA ? 'B' : 'tie';
        
        let analysis = '';
        if (winner === 'tie') {
            analysis = `Ambos os veículos apresentam custo-benefício similar. ${
                betterRetention === 'tie' 
                    ? 'A retenção de valor é equivalente entre ambos.' 
                    : `O Veículo ${betterRetention} tem melhor retenção de valor, mas o preço compensa essa diferença.`
            } Considere outras preferências pessoais para a decisão final.`;
        } else {
            const winnerVehicle = winner === 'A' ? analysisA : analysisB;
            const loserVehicle = winner === 'A' ? analysisB : analysisA;
            const winnerPrice = winner === 'A' ? currentPriceA : currentPriceB;
            const loserPrice = winner === 'A' ? currentPriceB : currentPriceA;
            
            if (winnerPrice <= loserPrice) {
                analysis = `O Veículo ${winner} é a escolha ideal pois custa ${formatCurrency(priceDiff)} a menos e ${
                    betterRetention === winner ? 'ainda tem melhor retenção de valor.' : 'mantém boa retenção de valor.'
                } Você economiza na compra e terá menor perda com a desvalorização futura.`;
            } else {
                analysis = `O Veículo ${winner} custa ${formatCurrency(priceDiff)} a mais, mas compensa com ${
                    betterRetention === winner ? 'retenção de valor superior' : 'melhor custo-benefício geral'
                }. A longo prazo, essa escolha pode representar economia devido à menor desvalorização.`;
            }
        }

        const result = {
            winner,
            vehicleA: {
                marca: analysisA.marca,
                modelo: analysisA.modelo,
                currentPrice: currentPriceA,
                totalDepreciation: totalDepA,
                avgYearlyDrop: avgYearlyDropA,
                yearRange: yearRangeA,
                priceEvolution: priceEvolutionA
            },
            vehicleB: {
                marca: analysisB.marca,
                modelo: analysisB.modelo,
                currentPrice: currentPriceB,
                totalDepreciation: totalDepB,
                avgYearlyDrop: avgYearlyDropB,
                yearRange: yearRangeB,
                priceEvolution: priceEvolutionB
            },
            scores: {
                A: Math.round(scoreA),
                B: Math.round(scoreB)
            },
            comparisonTable,
            analysis
        };

        return json(result);

    } catch (e: any) {
        console.error('Compare error:', e);
        throw error(e.status || 500, e.message || 'Erro interno na comparação');
    }
};

function formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}
