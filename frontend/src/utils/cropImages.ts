export const getCropImageUrl = (cropName: string): string => {
  const normalized = cropName.toLowerCase().trim();

  const map: Record<string, string> = {
    rice: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0a/20201102.Hengnan.Hybrid_rice_Sanyou-1.6.jpg/960px-20201102.Hengnan.Hybrid_rice_Sanyou-1.6.jpg',
    maize: 'https://upload.wikimedia.org/wikipedia/commons/e/e3/Zea_mays_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-283.jpg',
    chickpea: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/89/Chickpea_BNC.jpg/960px-Chickpea_BNC.jpg',
    kidneybeans: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/27/Red_Rajma_BNC.jpg/960px-Red_Rajma_BNC.jpg',
    pigeonpeas: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/92/Cajanus_cajan_Blanco1.167-cropped.jpg/960px-Cajanus_cajan_Blanco1.167-cropped.jpg',
    mothbeans: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/86/Mung_beans_%28Vigna_radiata%29.jpg/960px-Mung_beans_%28Vigna_radiata%29.jpg',
    mungbean: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/86/Mung_beans_%28Vigna_radiata%29.jpg/960px-Mung_beans_%28Vigna_radiata%29.jpg',
    blackgram: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6f/Black_gram.jpg/960px-Black_gram.jpg',
    lentil: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f5/3_types_of_lentil.png/960px-3_types_of_lentil.png',
    pomegranate: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6a/Pomegranate_Juice_%282019%29.jpg/960px-Pomegranate_Juice_%282019%29.jpg',
    banana: 'https://upload.wikimedia.org/wikipedia/commons/d/de/Bananavarieties.jpg',
    mango: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/74/Mangos_-_single_and_halved.jpg/960px-Mangos_-_single_and_halved.jpg',
    grapes: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/53/Grapes%2C_Rostov-on-Don%2C_Russia.jpg/960px-Grapes%2C_Rostov-on-Don%2C_Russia.jpg',
    watermelon: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/47/Taiwan_2009_Tainan_City_Organic_Farm_Watermelon_FRD_7962.jpg/960px-Taiwan_2009_Tainan_City_Organic_Farm_Watermelon_FRD_7962.jpg',
    muskmelon: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/ff/Muskmelon.jpg/960px-Muskmelon.jpg',
    apple: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a6/Pink_lady_and_cross_section.jpg/960px-Pink_lady_and_cross_section.jpg',
    orange: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e3/Oranges_-_whole-halved-segment.jpg/960px-Oranges_-_whole-halved-segment.jpg',
    papaya: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/84/Carica_papaya_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-029.jpg/960px-Carica_papaya_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-029.jpg',
    coconut: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Cocos_nucifera_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-187.jpg/960px-Cocos_nucifera_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-187.jpg',
    cotton: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/68/CottonPlant.JPG/960px-CottonPlant.JPG',
    jute: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/84/Jute_-_Kolkata_2003-10-31_00538.JPG/960px-Jute_-_Kolkata_2003-10-31_00538.JPG',
    coffee: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e4/Latte_and_dark_coffee.jpg/960px-Latte_and_dark_coffee.jpg',
  };

  // Try exact match first
  if (map[normalized]) return map[normalized];

  // Try partial match
  for (const key in map) {
    if (normalized.includes(key) || key.includes(normalized)) {
      return map[key];
    }
  }

  // Fallback generic farming image
  return 'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&q=80&w=800';
};
