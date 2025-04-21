document.addEventListener("DOMContentLoaded", () => {
  const productsContainer = document.querySelector("#products-container");

  async function fetchProducts() {
    try {
      const response = await fetch("http://localhost:8000/products/");
      if (!response.ok) {
        throw new Error("Failed to fetch products");
      }
      const products = await response.json();
      renderProducts(products);
    } catch (error) {
      console.error(error);
      productsContainer.innerHTML = "<p class='text-red-500'>Failed to load products.</p>";
    }
  }

  function renderProducts(products) {
    productsContainer.innerHTML = "";
    products.forEach((product) => {
      const productCard = document.createElement("div");
      productCard.className = "bg-white rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer";
      productCard.innerHTML = `
        <img src="${product.image_url || 'https://via.placeholder.com/300x200'}" alt="${product.title}" class="rounded-md mb-4 w-full object-cover" />
        <h4 class="font-semibold mb-1">${product.title}</h4>
        <p class="text-indigo-600 font-bold mb-1">$${product.price.toFixed(2)}</p>
        <p class="text-gray-500 text-sm">Seller ID: ${product.owner_id}</p>
      `;
      productsContainer.appendChild(productCard);
    });
  }

  fetchProducts();
});
