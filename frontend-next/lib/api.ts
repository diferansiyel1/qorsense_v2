import axios from 'axios';
import { AnalysisResult, SensorDataInput, SyntheticRequest, SyntheticResponse } from '@/types';

const API_URL = 'http://localhost:8000';

export const api = {
    healthCheck: async () => {
        try {
            const res = await axios.get(`${API_URL}/`);
            return res.status === 200;
        } catch (error) {
            return false;
        }
    },

    generateSynthetic: async (req: SyntheticRequest): Promise<number[]> => {
        const res = await axios.post<SyntheticResponse>(`${API_URL}/generate-synthetic`, req);
        return res.data.data;
    },

    analyze: async (data: SensorDataInput): Promise<AnalysisResult> => {
        const res = await axios.post<AnalysisResult>(`${API_URL}/analyze`, data);
        return res.data;
    },

    generateReport: async (result: AnalysisResult, rawData: number[]) => {
        const payload = { ...result, data: rawData };
        const res = await axios.post(`${API_URL}/report`, payload, {
            responseType: 'blob',
        });
        return res.data;
    }
};
