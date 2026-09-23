export const getCropImageUrl = (cropName: string): string => {
  const normalized = cropName.toLowerCase().trim();
  
  const map: Record<string, string> = {
    rice: 'https://images.unsplash.com/photo-1586771107565-962cbce4e4ba?auto=format&fit=crop&q=80&w=800',
    paddy: 'https://images.unsplash.com/photo-1586771107565-962cbce4e4ba?auto=format&fit=crop&q=80&w=800',
    wheat: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=800',
    maize: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&q=80&w=800',
    corn: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&q=80&w=800',
    cotton: 'https://images.unsplash.com/photo-1584852951717-d5d1c2386a34?auto=format&fit=crop&q=80&w=800',
    sugarcane: 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&q=80&w=800',
    soybean: 'https://images.unsplash.com/photo-1627926210332-9ec9bc8a5c32?auto=format&fit=crop&q=80&w=800',
    groundnut: 'https://images.unsplash.com/photo-1598460592963-718693c0dae8?auto=format&fit=crop&q=80&w=800',
    mustard: 'https://images.unsplash.com/photo-1522067784013-4333b2a59a72?auto=format&fit=crop&q=80&w=800',
    millet: 'https://images.unsplash.com/photo-1630138905389-9134a6ef537d?auto=format&fit=crop&q=80&w=800',
    jute: 'https://images.unsplash.com/photo-1616886477042-3e2b20fb97a1?auto=format&fit=crop&q=80&w=800',
    chickpea: 'https://images.unsplash.com/photo-1574516629949-aebba827f714?auto=format&fit=crop&q=80&w=800',
    barley: 'https://images.unsplash.com/photo-1537233880468-b3d2b272fdf8?auto=format&fit=crop&q=80&w=800',
    tea: 'https://images.unsplash.com/photo-1556881286-fc6915169721?auto=format&fit=crop&q=80&w=800',
    coffee: 'https://images.unsplash.com/photo-1551699933-2586a11e2f5b?auto=format&fit=crop&q=80&w=800',
    apple: 'https://images.unsplash.com/photo-1560806887-1e4cd0b6fac6?auto=format&fit=crop&q=80&w=800',
    banana: 'https://images.unsplash.com/photo-1528825871115-3581a5387919?auto=format&fit=crop&q=80&w=800',
    mango: 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&q=80&w=800',
    grapes: 'https://images.unsplash.com/photo-1596363505729-f4204531d5eb?auto=format&fit=crop&q=80&w=800',
    orange: 'https://images.unsplash.com/photo-1557800636-894a64c1696f?auto=format&fit=crop&q=80&w=800',
    papaya: 'https://images.unsplash.com/photo-1617112848923-cc2234394a8a?auto=format&fit=crop&q=80&w=800',
    coconut: 'https://images.unsplash.com/photo-1526424382096-74a93e105682?auto=format&fit=crop&q=80&w=800',
    pomegranate: 'https://images.unsplash.com/photo-1528659173007-8e65e6ebc45a?auto=format&fit=crop&q=80&w=800',
  };

  for (const key in map) {
    if (normalized.includes(key)) {
      return map[key];
    }
  }

  // Fallback generic farming image
  return 'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&q=80&w=800';
};
