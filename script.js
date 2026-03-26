// State Management
let currentAction = 'BUY';
let activeStock = { name: 'AAPL', price: 150.0 };

const stocks = [
    { name: 'RELIANCE', price: 2945.50, change: '+0.42%' },
    { name: 'TCS', price: 3910.15, change: '-1.20%' },
    { name: 'HDFC BANK', price: 1420.00, change: '+0.15%' },
    { name: 'INFY', price: 1605.40, change: '-0.85%' },
    { name: 'ZOMATO', price: 185.20, change: '+3.40%' }
];

// Initialize the Application
document.addEventListener('DOMContentLoaded', () => {
    // Check if logged in (simple check, in real app use session)
    if (localStorage.getItem('loggedIn')) {
        showTrading();
    } else {
        showLogin();
    }

    // Form listeners are handled via normal form action POST now

    renderWatchlist();
    // Connect to backend
    const socket = io();
    socket.on('stock_update', function(data) {
        for (const [symbol, price] of Object.entries(data)) {
            const stock = stocks.find(s => s.name === symbol);
            if (stock) {
                stock.price = price;
            }
        }
        renderWatchlist();
        // Update active stock price if it's the one we are looking at
        const liveMatch = stocks.find(s => s.name === activeStock.name);
        if (liveMatch) {
            document.getElementById('active-price').innerText = `$${liveMatch.price.toFixed(2)}`;
            updateMargin();
        }
    });
});

function showLogin() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('register-section').classList.add('hidden');
    document.getElementById('trading-section').classList.add('hidden');
}

function showRegister() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('register-section').classList.remove('hidden');
    document.getElementById('trading-section').classList.add('hidden');
}

function showTrading() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('register-section').classList.add('hidden');
    document.getElementById('trading-section').classList.remove('hidden');
    document.getElementById('profile-section').classList.add('hidden');
}

function showProfile() {
    fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            document.getElementById('profile-username').textContent = data.username;
            document.getElementById('profile-email').textContent = data.email;
            document.getElementById('profile-balance').textContent = Number(data.balance).toFixed(2);
            const portfolioEl = document.getElementById('profile-portfolio');
            portfolioEl.innerHTML = '';
            // /api/profile currently returns only username/email/balance, so portfolio can be fetched separately if needed
            document.getElementById('trading-section').classList.add('hidden');
            document.getElementById('profile-section').classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            alert('Error loading profile');
        });
}

function logout() {
    fetch('/logout');
    localStorage.removeItem('loggedIn');
    showLogin();
}

async function handleLogin(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (response.ok && data.success) {
            localStorage.setItem('loggedIn', 'true');
            showTrading();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error.');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    try {
        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert('Registration successful. Please login.');
            showLogin();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error.');
    }
}

function renderWatchlist() {
    const watchlistEl = document.getElementById('watchlist');
    watchlistEl.innerHTML = ''; // Clear existing

    stocks.forEach(stock => {
        const div = document.createElement('div');
        div.className = 'watchlist-item p-4 border-b flex justify-between cursor-pointer';
        div.innerHTML = `
            <div>
                <p class="font-bold text-sm">${stock.name}</p>
                <p class="text-xs text-gray-400">NSE</p>
            </div>
            <div class="text-right">
                <p class="font-mono text-sm ${stock.change.includes('+') ? 'text-green-500' : 'text-red-500'}">
                    ₹${stock.price.toFixed(2)}
                </p>
                <p class="text-xs text-gray-400">${stock.change}</p>
            </div>
        `;
        div.onclick = () => selectStock(stock);
        watchlistEl.appendChild(div);
    });
}

function selectStock(stock) {
    activeStock = stock;
    document.getElementById('active-symbol').innerText = stock.name;
    document.getElementById('active-price').innerText = `$${stock.price.toFixed(2)}`;
    document.getElementById('order-price').value = stock.price.toFixed(2);
    updateMargin();
}

function setOrderType(type) {
    currentAction = type;
    const btn = document.getElementById('exec-btn');
    const buyTog = document.getElementById('buy-toggle');
    const sellTog = document.getElementById('sell-toggle');

    if(type === 'BUY') {
        btn.className = "w-full py-3 rounded-lg text-white font-bold btn-buy shadow-lg transition-all";
        btn.innerText = "PLACE BUY ORDER";
        buyTog.classList.add('btn-buy', 'text-white');
        sellTog.classList.remove('btn-sell', 'text-white');
    } else {
        btn.className = "w-full py-3 rounded-lg text-white font-bold btn-sell shadow-lg transition-all";
        btn.innerText = "PLACE SELL ORDER";
        sellTog.classList.add('btn-sell', 'text-white');
        buyTog.classList.remove('btn-buy', 'text-white');
    }
}

function updateMargin() {
    const qty = document.getElementById('order-qty').value;
    const price = activeStock.price;
    const total = (qty * price).toLocaleString('en-US', { maximumFractionDigits: 2 });
    document.getElementById('margin-total').innerText = `$${total}`;
}

// Simulate Market Movement
function simulateMarket() {
    stocks.forEach(s => {
        const move = (Math.random() - 0.5) * 5; // Random move between -2.5 and +2.5
        s.price += move;
    });
    renderWatchlist();
    // Update active stock price if it's the one we are looking at
    const liveMatch = stocks.find(s => s.name === activeStock.name);
    document.getElementById('active-price').innerText = `₹${liveMatch.price.toFixed(2)}`;
    updateMargin();
}

// Integration with Python Backend
async function executeTrade() {
    const formData = new FormData();
    formData.append('symbol', activeStock.name);
    formData.append('quantity', document.getElementById('order-qty').value);

    const url = currentAction === 'BUY' ? '/buy' : '/sell';

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert(data.message);
        } else {
            alert(data.error || 'Trade failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    }
}
