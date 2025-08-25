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
    
    // Function to update URL parameters
    const updateURL = (search, category) => {
        const params = new URLSearchParams();
        if (search) params.set('search', search);
        if (category) params.set('category', category);
        
        const newURL = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
        window.history.pushState({}, '', newURL);
    };
    
    // Function to read URL parameters on load
    const readURLParams = () => {
        const params = new URLSearchParams(window.location.search);
        const search = params.get('search') || '';
        const category = params.get('category') || '';
        setSearchTerm(search);
        setSelectedCategory(category);
    };
    const [selectedItem, setSelectedItem] = useState(null);
    const [loading, setLoading] = useState(true);

    // Load wardrobe data and URL parameters on mount
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
                // Read URL parameters after data loads
                readURLParams();
            })
            .catch(error => {
                console.error('Error loading wardrobe data:', error);
                console.error('Response might be HTML instead of JSON. Check nginx configuration.');
                setLoading(false);
            });
    }, []);
    
    // Update URL when search term or category changes
    useEffect(() => {
        if (wardrobeData) { // Only update URL after data is loaded
            updateURL(searchTerm, selectedCategory);
        }
    }, [searchTerm, selectedCategory, wardrobeData]);

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
            // Also read URL parameters when navigating back/forward
            readURLParams();
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
                <h1>My Wardrobe Collection!</h1>
                <p>
                    {filteredItems.length === wardrobeData.metadata.total_items 
                        ? `${wardrobeData.metadata.total_items} items in your wardrobe`
                        : `${filteredItems.length} out of ${wardrobeData.metadata.total_items} items shown`
                    }
                </p>
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
