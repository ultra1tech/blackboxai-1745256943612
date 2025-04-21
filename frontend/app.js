// Constants
const API_URL = 'http://localhost:8000';

// Authentication Functions
function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

function getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred');
        }

        return data;
    } catch (error) {
        showAlert('error', error.message);
        throw error;
    }
}

// Alert Component
function showAlert(type, message, duration = 3000) {
    const alert = document.getElementById('alert');
    if (!alert) {
        console.error('Alert element not found');
        return;
    }

    const alertContent = alert.querySelector('div');
    alertContent.className = 'rounded-md p-4 ' + 
        (type === 'error' ? 'bg-red-50 text-red-800' : 'bg-green-50 text-green-800');
    alertContent.textContent = message;
    
    alert.classList.remove('hidden');
    setTimeout(() => alert.classList.add('hidden'), duration);
}

// Form Validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function validateRequired(value) {
    return value && value.trim().length > 0;
}

// Currency Formatter
const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
});

function formatCurrency(amount) {
    return currencyFormatter.format(amount);
}

// Date Formatter
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Image Upload Helper
async function uploadImage(file, endpoint) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to upload image');
        }

        return await response.json();
    } catch (error) {
        showAlert('error', error.message);
        throw error;
    }
}

// Debounce Helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Cart Management
const cart = {
    items: JSON.parse(localStorage.getItem('cart') || '[]'),

    addItem(product, quantity = 1) {
        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({
                id: product.id,
                title: product.title,
                price: product.price,
                image: product.image_urls ? JSON.parse(product.image_urls)[0] : null,
                quantity
            });
        }
        
        this.save();
        this.updateUI();
    },

    removeItem(productId) {
        this.items = this.items.filter(item => item.id !== productId);
        this.save();
        this.updateUI();
    },

    updateQuantity(productId, quantity) {
        const item = this.items.find(item => item.id === productId);
        if (item) {
            item.quantity = quantity;
            if (quantity <= 0) {
                this.removeItem(productId);
            } else {
                this.save();
                this.updateUI();
            }
        }
    },

    clear() {
        this.items = [];
        this.save();
        this.updateUI();
    },

    getTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    },

    getCount() {
        return this.items.reduce((count, item) => count + item.quantity, 0);
    },

    save() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    },

    updateUI() {
        // Update cart count in header
        const cartCount = document.getElementById('cartCount');
        if (cartCount) {
            cartCount.textContent = this.getCount();
        }

        // Update cart total if on cart page
        const cartTotal = document.getElementById('cartTotal');
        if (cartTotal) {
            cartTotal.textContent = formatCurrency(this.getTotal());
        }

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: {
                items: this.items,
                total: this.getTotal(),
                count: this.getCount()
            }
        }));
    }
};

// Wishlist Management
const wishlist = {
    items: new Set(JSON.parse(localStorage.getItem('wishlist') || '[]')),

    async toggle(productId) {
        try {
            if (this.items.has(productId)) {
                await apiRequest(`/api/wishlists/${productId}`, { method: 'DELETE' });
                this.items.delete(productId);
            } else {
                await apiRequest('/api/wishlists', {
                    method: 'POST',
                    body: JSON.stringify({ product_id: productId })
                });
                this.items.add(productId);
            }
            
            this.save();
            this.updateUI();
            return true;
        } catch (error) {
            console.error('Error toggling wishlist:', error);
            return false;
        }
    },

    has(productId) {
        return this.items.has(productId);
    },

    save() {
        localStorage.setItem('wishlist', JSON.stringify([...this.items]));
    },

    updateUI() {
        // Update wishlist buttons
        document.querySelectorAll('[data-wishlist-id]').forEach(button => {
            const productId = parseInt(button.dataset.wishlistId);
            button.classList.toggle('text-red-600', this.has(productId));
        });

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('wishlistUpdated', {
            detail: {
                items: [...this.items]
            }
        }));
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize cart UI
    cart.updateUI();
    
    // Initialize wishlist UI
    wishlist.updateUI();
    
    // Setup authentication check
    if (document.body.dataset.requiresAuth && !isAuthenticated()) {
        window.location.href = '/login.html';
    }
});

// Export utilities
export {
    apiRequest,
    showAlert,
    validateEmail,
    validatePassword,
    validateRequired,
    formatCurrency,
    formatDate,
    uploadImage,
    debounce,
    cart,
    wishlist,
    isAuthenticated,
    getCurrentUser,
    logout
};
