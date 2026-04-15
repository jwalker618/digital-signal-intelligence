/**
 * Shared utilities used across all tabs.
 */

export const getJSONBItems = (
  data: Record<string, any> | null | undefined,
) => {
  if (!data) return [];

  // Map entries into a flat object structure { name: string, ...details } and return
  return Object.entries(data).map(([key, value]) => ({
    name: key,
    ...value,
  }));
};

export const getSortedItems = (
  data: Record<string, any> | null | undefined,
  sortBy: string | null = null,
  parentExclude: string | null = null,
) => {

  const items = getJSONBItems(data);

  const filteredItems = parentExclude ? items.filter((item) => item.name !== parentExclude) : items;

  if (!sortBy) return filteredItems;
  
  return filteredItems.sort((a, b) => (b[sortBy] ?? 0) - (a[sortBy] ?? 0));
};

export const getOtherRow = (
  data: any[] | null | undefined, 
  sumKeys: string[],              
  limit: number = 3,              
) => {
  if (!data || !Array.isArray(data)) return [];

  const others = data.slice(limit);

  if (others.length > 0) {
    const othersRow = {
      name: 'Others',
      ...sumKeys.reduce((acc, key) => ({
        ...acc,
        [key]: others.reduce((sum, curr) => sum + (curr[key] || 0), 0)
      }), {})
    };
    return [othersRow];
  }
  
  return [];
};
