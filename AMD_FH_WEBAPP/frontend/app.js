/**
 * StayHeal - Frontend Application Logic
 * Handles API integration, Health Scoring, and dynamic UI updates.
 */

// --- Configuration ---
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000', // Default, real one fetched from .env if possible
    USER_ID: 'user_123_demo'
};

// --- State Management ---
let currentMenu = [];
let cart = [];
let userHistory = [];

// --- Initialisation ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("StayHeal Initialising...");
    await loadInitialData();
});

async function loadInitialData() {
    // 1. Mock Menu Items (Normally would come from a database/partner API)
    currentMenu = [
        { id: "itm_001", name: "Quinoa Harvest Bowl", calories: 350, protein: 18, sugar: 4, price: 349, image_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuB7w4iNFmrPGrUBJXh5n0Sxw6dkXk1nAOvNKRKzJrLFzqRLaRTyUXVlUnlhv0BGizbq5AX0G1pJIFLgbWToSjOfNfQHafEDaMAp9HvouweXtOppQcFbjb4uk0jy74UXvFQ0OJTwrkRg1A0jdkiBLGLy26tPzKoWg5ZhBXg9Umm-b15t9cGjTn2TMpyvbXlbC8GtvL0TbtoSHAcYVBMtB09FIt6iHNuu0UTtiBjNZbUGZhb-dYOWr7ke9R4193Xkkvet8H-XVLWyWmA" },
        { id: "itm_002", name: "Double Cheese Pizza", calories: 950, protein: 25, sugar: 8, price: 599, image_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCKc0awBA5JVEHBvPdgRL-wVs3yvLX4UgM1as2RHl5_EPwZC174SjCB57n2Jpi2lp-S4lyJaMusJqJU5BLxAWYZa-Zk0URuXOHRzhVEb7770o7ltSXzLn_KbROa3B6yBVyXjVeCWewJgZnCGzJrc0I4lOh7l-As56kXd5-0lLBTxGvuE_h_4b8j2AHfvGzWUEJH3kmVfk-U4NQBKdl0ZlJ99tt_6QeiZ1WaoWNnwwWx45hoDve5D5UyM3FQocyMIC57E3hFNwyFE1M" },
        { id: "itm_003", name: "Grilled Chicken Salad", calories: 420, protein: 32, sugar: 6, price: 485, image_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuBMjzu-b3bDdmqe1KA3JW_ucWH0EqAmKmPwXvtGKPGdQJ3peG5LswKZks6MKktAw-dFHJjzUMkk8VqgJQBXlqwsc3bgTEChX5d0RjSGoRrcgNoYymUQlbANav1EhkK4hebLz9M2Wyg363GNqYuQZGvQrC5nzEWrPO1azfy_n-9V1xLIq1U3-PSiuJLiVYixY6G23oEbCcm5ewGYnXEjXK_UzcLFetLAXKsdMpy7tbKDYjQo61SfeqqrOtGJzjUlo4FcXf_9ITmWTDE" },
        { id: "itm_004", name: "Chocolate Lava Cake", calories: 600, protein: 4, sugar: 45, price: 299, image_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuAVI6CYnwSAotyshsIyp-D100bIfePx9rm2MPjMWc5ps3Hp0yIUlm_PhmxXAU_jF2V2202upqrE6sTZAv3Sx7s0lwHTwCyjCZNQ10NEkcaq3GfzixYYfTRvkRd7CiWcv3c_LBEBmeC0S2pDMRMRfN48JbZqs-Q1cxPYUV-ANu_ZtTMHgqMG9IeShDJ8_4-mhAxCrRTdbKcowG5Kuk6WrrqEM8DJFG0_aAiNxQeYFsmDWGjXFy4pKxnbTeZuIqFpjl0WdPJSMe8dtS8" }
    ];

    await getRecommendations();
}

// --- API Interactions ---

async function getRecommendations() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: CONFIG.USER_ID,
                menu_items: currentMenu,
                context: {
                    hour: new Date().getHours(),
                    goal: "Workout Fuel"
                }
            })
        });

        if (!response.ok) throw new Error("Backend unreachable");

        const data = await response.json();
        renderMenu(data.ranked_items);
    } catch (error) {
        console.warn("Using fallback scoring due to error:", error);
        // If backend fails, use a simplified local scoring for demonstration
        const fallback = currentMenu.map(item => ({
            ...item,
            health_score: item.calories < 500 ? 80 : 30,
            badge: item.calories < 500 ? "green" : "red",
            is_top_pick: false
        }));
        renderMenu(fallback);
    }
}

async function getNudgeMessage() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/nudge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_history: userHistory })
        });
        const data = await response.json();
        return data.message;
    } catch (e) {
        return "Variety is key to a healthy lifestyle!";
    }
}

// --- UI Rendering ---

function renderMenu(items) {
    const container = document.getElementById('menu-container');
    if (!container) return;

    container.innerHTML = '';
    items.forEach(item => {
        const card = document.createElement('div');
        card.className = "group bg-surface-container-lowest rounded-[1.5rem] overflow-hidden shadow-[0_12px_24px_rgba(0,0,0,0.02)] border border-outline-variant/10 transition-transform hover:-translate-y-1";
        
        const badgeColor = item.badge === 'green' ? 'tertiary' : (item.badge === 'yellow' ? 'secondary' : 'error');
        const badgeText = item.health_score + " Health Score";

        card.innerHTML = `
            <div class="relative h-48 overflow-hidden">
                <img class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" src="${item.image_url}" alt="${item.name}">
                <div class="absolute top-4 right-4 bg-white/80 backdrop-blur-md px-3 py-1.5 rounded-full flex items-center gap-2">
                    <span class="material-symbols-outlined text-${badgeColor} text-sm" style="font-variation-settings: 'FILL' 1;">verified</span>
                    <span class="text-on-surface font-bold text-sm tracking-tight">${badgeText}</span>
                </div>
                ${item.is_top_pick ? `
                <div class="absolute top-4 left-4 bg-primary text-white px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg">
                    ✦ Better Choice
                </div>` : ''}
            </div>
            <div class="p-6">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="text-xl font-bold text-on-surface">${item.name}</h4>
                        <p class="text-on-surface-variant text-sm">${item.calories} kcal • ${item.protein}g Protein</p>
                    </div>
                    <span class="text-primary font-bold text-lg">₹${item.price}</span>
                </div>
                <button onclick="addToCart('${item.id}', ${item.health_score})" class="mt-4 w-full bg-secondary text-white py-3 rounded-full font-bold text-sm hover:opacity-90 active:scale-95 transition-all">
                    Add to Cart
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

// --- Action Handlers ---

window.addToCart = function(itemId, score) {
    console.log(`Adding ${itemId} to cart. Score: ${score}`);
    
    if (score < 40) {
        showNudgeModal(itemId);
    } else {
        processAddToCart(itemId);
    }
};

function showNudgeModal(itemId) {
    const modal = document.getElementById('nudge-modal');
    const item = currentMenu.find(i => i.id === itemId);
    
    document.getElementById('nudge-item-name').innerText = item.name;
    modal.classList.add('active');
}

window.closeNudgeModal = function() {
    document.getElementById('nudge-modal').classList.remove('active');
};

window.addAnyway = function() {
    // Hidden logic for "Add Anyway"
    const modal = document.getElementById('nudge-modal');
    modal.classList.remove('active');
    alert("Added to cart! Remember to balance this with a healthy snack tomorrow.");
};

window.seeAlternatives = function() {
    closeNudgeModal();
    // Scroll to the top recommended item
    const topPick = document.querySelector('.bg-primary.text-white');
    if (topPick) {
        topPick.scrollIntoView({ behavior: 'smooth', block: 'center' });
        topPick.parentElement.parentElement.classList.add('ring-4', 'ring-primary/20');
        setTimeout(() => {
            topPick.parentElement.parentElement.classList.remove('ring-4', 'ring-primary/20');
        }, 3000);
    }
};

function processAddToCart(itemId) {
    alert("Added to cart!");
}
