const { useState, useEffect } = React;

// Item Card Component
const ItemCard = ({ item, onClick }) => (
    <div className="item-card" onClick={() => onClick(item)}>
        <img 
            src={item.thumbnail} 
            alt={item.title}
            className="item-thumbnail"
        />
        <div className="item-info">
            <h3 className="item-title">{item.title}</h3>
            <span className="item-category">{item.category}</span>
            <div className="item-tags">
                {item.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                ))}
            </div>
        </div>
    </div>
);

// Item Details Modal Component
const ItemDetails = ({ item, onClose }) => {
    if (!item) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="close-button" onClick={onClose}>×</button>
                <div className="item-details">
                    <img 
                        src={item.image} 
                        alt={item.title}
                        className="item-full-image"
                    />
                    <div className="item-info-panel">
                        <h2>{item.title}</h2>
                        <p className="category">Category: {item.category}</p>
                        
                        <div className="tags-section">
                            <h4>Tags:</h4>
                            <div className="tags">
                                {item.tags.map((tag, index) => (
                                    <span key={index} className="tag">{tag}</span>
                                ))}
                            </div>
                        </div>
                        
                        {item.notes && (
                            <div className="notes-section">
                                <h4>Notes:</h4>
                                <p>{item.notes}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

// Search and Filter Component
const SearchFilters = ({ searchTerm, setSearchTerm, selectedCategory, setSelectedCategory, categories }) => (
    <div className="search-filters">
        <div className="search-bar">
            <input
                type="text"
                placeholder="Search items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
            />
        </div>
        
        <div className="category-filter">
            <select 
                value={selectedCategory} 
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="category-select"
            >
                <option value="">All Categories</option>
                {categories.map(category => (
                    <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                    </option>
                ))}
            </select>
        </div>
    </div>
);

// Main App Component
const App = () => {
    const [wardrobeData, setWardrobeData] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedItem, setSelectedItem] = useState(null);
    const [loading, setLoading] = useState(true);

    // Load wardrobe data
    useEffect(() => {
        fetch('wardrobe_data.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                setWardrobeData(data);
                setLoading(false);
            })
            .catch(error => {
                console.error('Error loading wardrobe data:', error);
                console.error('Response might be HTML instead of JSON. Check nginx configuration.');
                setLoading(false);
            });
    }, []);

    // Filter items based on search and category
    const filteredItems = wardrobeData?.items?.filter(item => {
        const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            item.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
        const matchesCategory = !selectedCategory || item.category === selectedCategory;
        return matchesSearch && matchesCategory;
    }) || [];

    const handleItemClick = (item) => {
        setSelectedItem(item);
        // Update URL without page reload
        window.history.pushState({}, '', `#/item/${item.slug}`);
    };

    const handleCloseModal = () => {
        setSelectedItem(null);
        window.history.pushState({}, '', '#/');
    };

    // Handle browser back/forward
    useEffect(() => {
        const handlePopState = () => {
            const hash = window.location.hash;
            if (hash.startsWith('#/item/')) {
                const slug = hash.replace('#/item/', '');
                const item = wardrobeData?.items?.find(item => item.slug === slug);
                setSelectedItem(item || null);
            } else {
                setSelectedItem(null);
            }
        };

        window.addEventListener('popstate', handlePopState);
        handlePopState(); // Handle initial load

        return () => window.removeEventListener('popstate', handlePopState);
    }, [wardrobeData]);

    if (loading) {
        return <div className="loading">Loading your wardrobe...</div>;
    }

    if (!wardrobeData) {
        return <div className="error">Error loading wardrobe data</div>;
    }

    return (
        <div className="app">
            <header className="app-header">
                <h1>My Wardrobe Collection</h1>
                <p>{wardrobeData.metadata.total_items} items in your wardrobe</p>
            </header>

            <SearchFilters 
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                selectedCategory={selectedCategory}
                setSelectedCategory={setSelectedCategory}
                categories={wardrobeData.categories}
            />

            <div className="items-grid">
                {filteredItems.map(item => (
                    <ItemCard 
                        key={item.id} 
                        item={item} 
                        onClick={handleItemClick}
                    />
                ))}
            </div>

            {filteredItems.length === 0 && (
                <div className="no-results">
                    No items found matching your search criteria.
                </div>
            )}

            <ItemDetails 
                item={selectedItem} 
                onClose={handleCloseModal}
            />
        </div>
    );
};

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));