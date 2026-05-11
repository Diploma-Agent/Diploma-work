import React, { createContext, useContext, useRef, useCallback } from 'react';
import { financeService } from '../api/financeService';

const FinanceContext = createContext(null);

// TTL кешу — 5 хвилин
const CACHE_TTL = 5 * 60 * 1000;

export function FinanceProvider({ children }) {
    const cache = useRef({});

    const getToken = () => localStorage.getItem('token');

    /** Повертає закешовані дані або fetchFn() якщо кеш застарів */
    const withCache = useCallback(async (key, fetchFn) => {
        const entry = cache.current[key];
        if (entry && Date.now() - entry.ts < CACHE_TTL) {
            return entry.data;
        }
        const data = await fetchFn();
        cache.current[key] = { data, ts: Date.now() };
        return data;
    }, []);

    /** Скидає конкретний або всі ключі кешу */
    const invalidate = useCallback((key = null) => {
        if (key) delete cache.current[key];
        else cache.current = {};
    }, []);

    // ── Публічні методи ────────────────────────────────────────────────────────

    const getTransactions = useCallback((source = 'all', days = 30, dateFrom = '', dateTo = '', connectionIds = [], sources = []) => {
        const idsKey = connectionIds.length > 0 ? connectionIds.sort().join(',') : '';
        const srcKey = sources.length > 0 ? sources.sort().join(',') : source;
        const key = `tx:${srcKey}:${days}:${dateFrom}:${dateTo}:${idsKey}`;
        return withCache(key, () =>
            financeService.getTransactions(getToken(), source, days, dateFrom, dateTo, connectionIds, sources)
        );
    }, [withCache]);

    const getBalance = useCallback(() =>
        withCache('balance', () => financeService.getBankAnalytics(getToken()))
    , [withCache]);

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

export function useFinance() {
    const ctx = useContext(FinanceContext);
    if (!ctx) throw new Error('useFinance must be used inside FinanceProvider');
    return ctx;
}
