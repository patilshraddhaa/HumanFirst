import { useQuery } from "@tanstack/react-query";
import { getHealthz } from "../client/sdk.gen";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await getHealthz();
      return res.data;
    },
  });
}
