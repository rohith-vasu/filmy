import { create } from "zustand";
import { userAPI } from "@/lib/api";

interface StatsState {
    stats: any;
    fetchStats: () => Promise<void>;
}

export const useStatsStore = create<StatsState>((set) => ({
    stats: null,
    fetchStats: async () => {
        try {
            const res = await userAPI.stats();
            if (res.data?.status === "success") {
                set({ stats: res.data.data });
            }
        } catch (err) {
            console.error("Failed to fetch stats", err);
        }
    },
}));
