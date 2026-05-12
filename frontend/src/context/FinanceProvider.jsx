import React, { useRef, useCallback } from 'react';
import { financeService } from '../api/financeService';
import { FinanceContext } from './FinanceContext';

const CACHE_TTL = 5 * 60 * 1000;

export function FinanceProvider({ children }) {
    const cache = useRef({});

    const getToken = () => localStorage.getItem('token');
    
    const withCache = useCallback(async (key, fetchFn) => {
        const entry = cache.current[key];
        if (entry && Date.now() - entry.ts < CACHE_TTL) {
            return entry.data;
        }
        const data = await fetchFn();
        cache.current[key] = { data, ts: Date.now() };
        return data;
    }, []);

    const invalidate = useCallback((key = null) => {
        if (key) delete cache.current[key];
        else cache.current = {};
    }, []);

    const getTransactions = useCallback((source = 'all', days = 30, dateFrom = '', dateTo = '', connectionIds = [], sources = []) => {
        const idsKey = connectionIds.length > 0 ? connectionIds.sort().join(',') : '';
        const srcKey = sources.length > 0 ? sources.sort().join(',') : source;
        const key = `tx:${srcKey}:${days}:${dateFrom}:${dateTo}:${idsKey}`;
        return withCache(key, () =>
            financeService.getTransactions(getToken(), source, days, dateFrom, dateTo, connectionIds, sources)
        );
    }, [withCache]);

    const getBalance = useCallback((connectionIds = []) => {
        const key = connectionIds.length > 0 ? `balance:${connectionIds.sort().join(',')}` : 'balance';
        return withCache(key, () => financeService.getBankAnalytics(getToken(), connectionIds));
    }, [withCache]);

    const getBanks = useCallback(() =>
        withCache('banks', () => financeService.getBanks(getToken()))
    , [withCache]);

    const getExchanges = useCallback(() =>
        withCache('exchanges', () => financeService.getExchanges(getToken()))
    , [withCache]);

    return (
        <FinanceContext.Provider value={{
            getTransactions,
            getBalance,
            getBanks,
            getExchanges,
            invalidate,
        }}>
            {children}
        </FinanceContext.Provider>
    );
}