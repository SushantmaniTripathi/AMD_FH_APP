/**
 * StayHeal - High-Fidelity Frontend Application Logic
 */

const CONFIG = {
    API_BASE_URL: '',
    USER_ID: 'user_123_demo'
};

const MOCK_MENU = [
    { id: "itm_001", name: "Harissa Chicken & Quinoa", calories: 420, protein: 32, sugar: 4, price: 489, image_url: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80" },
    { id: "itm_002", name: "Lean Recovery Plate", calories: 350, protein: 40, sugar: 3, price: 340, image_url: "https://images.unsplash.com/photo-1532550907401-447e17424683?w=500&q=80" },
    { id: "itm_003", name: "Ahi Tuna Poke Bowl", calories: 310, protein: 28, sugar: 6, price: 520, image_url: "https://images.unsplash.com/photo-1548946522-4a313e8972a4?w=500&q=80" }
];

const MOCK_LOCAL_FAVORITES = [
    {
        name: "Tropical Açai Superbowl",
        restaurant: "Berry Bliss • 15-20 min",
        tag: "HIGH FIBER",
        price: 249,
        rating: 4.8,
        img: "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400&q=80"
    },
    {
        name: "Garden Pesto Flatbread",
        restaurant: "The Oven Health • 25 min",
        tag: "WHOLE GRAIN",
        price: 399,
        rating: 4.6,
        img: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=80"
    }
];

document.addEventListener('DOMContentLoaded', async () => {
    console.log("StayHeal V2 Initialising...");
    renderRecoveryMeals();
    renderLocalFavorites();
    await fetchHeroRecommendation();
});


// --- Dynamic UI Injections ---

function renderRecoveryMeals() {
    const container = document.getElementById('recovery-meals-container');
    if (!container) return;
    
    const meals = [
        { name: "Lean Recovery Plate", tag: "GLYCOGEN REFILL", price: 340, img: "https://images.unsplash.com/photo-1532550907401-447e17424683?w=500&q=80" },
        { name: "Ahi Tuna Poke Bowl", tag: "OMEGA-3 REPAIR", price: 520, img: "https://images.unsplash.com/photo-1548946522-4a313e8972a4?w=500&q=80" },
        { name: "Matcha Protein Shake", tag: "FAST ABSORB", price: 210, img: "https://images.unsplash.com/photo-1556881286-fc6915169721?w=500&q=80" }
    ];

    container.innerHTML = meals.map(meal => `
        <div class="min-w-[160px] snap-start flex flex-col gap-3">
            <div class="h-28 rounded-[1.2rem] overflow-hidden shadow-sm">
                <img src="${meal.img}" class="w-full h-full object-cover" alt="${meal.name}">
            </div>
            <div>
                <h5 class="text-[13px] font-['Manrope'] font-bold text-[#111827] leading-tight mb-1">${meal.name}</h5>
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-bold text-[#2E7D32] uppercase tracking-wider">${meal.tag}</span>
                    <span class="text-[11px] text-gray-500 font-medium">₹${meal.price}</span>
                </div>
            </div>
        </div>
    `).join('');
}


function renderLocalFavorites() {
    const container = document.getElementById('local-favorites-container');
    if (!container) return;

    container.innerHTML = MOCK_LOCAL_FAVORITES.map(fav => `
        <div class="flex items-center gap-4 bg-white p-3 rounded-[1.2rem] shadow-sm border border-gray-100/50">
            <!-- Thumbnail -->
            <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0">
                <img src="${fav.img}" class="w-full h-full object-cover" alt="${fav.name}">
            </div>
            
            <!-- Details -->
            <div class="flex-1 min-w-0">
                <h5 class="text-[14px] font-['Manrope'] font-bold text-[#111827] truncate mb-0.5">${fav.name}</h5>
                <p class="text-[10px] text-gray-500 truncate mb-1">${fav.restaurant}</p>
                <div class="flex items-center gap-1">
                    <span class="material-symbols-outlined text-[#2E7D32] text-[10px]" style="font-variation-settings: 'FILL' 1;">eco</span>
                    <span class="text-[8px] font-bold text-[#2E7D32] uppercase tracking-wider">${fav.tag}</span>
                </div>
            </div>
            
            <!-- Price & Rating -->
            <div class="flex flex-col items-end shrink-0 pl-2 border-l border-gray-100">
                <span class="text-[14px] font-bold text-[#111827] mb-0.5">₹${fav.price}</span>
                <div class="flex items-center gap-0.5 text-gray-400">
                    <span class="text-[10px] font-bold text-gray-500">${fav.rating}</span>
                    <span class="material-symbols-outlined text-[10px]" style="font-variation-settings: 'FILL' 1;">star</span>
                </div>
            </div>
        </div>
    `).join('');
}


// --- API Integrations ---

async function fetchHeroRecommendation() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: CONFIG.USER_ID,
                menu_items: MOCK_MENU,
                context: {
                    hour: new Date().getHours()
                }
            })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.ranked_items && data.ranked_items.length > 0) {
                // Assuming we dynamically update `#hero-recommendation` with data.ranked_items[0]
                // For this UI rebuild, we keep the styled skeleton and just log successful bind.
                console.log("Recommend API Bind Success! Top Pick: ", data.ranked_items[0].name);
            }
        }
    } catch (error) {
        console.warn("Backend not running or unreachable, falling back to mock UI.");
    }
}
