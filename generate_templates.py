"""
Script to generate remaining admin portal templates
"""

templates = {
    'menu_add.html': '''{% extends 'admin_portal/layout.html' %}

{% block title %}Add Menu Item - UAP Admin{% endblock %}

{% block content %}
<div class="max-w-3xl">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-2xl font-bold text-primary mb-6">Add New Menu Item</h3>
        
        <form method="POST" enctype="multipart/form-data" class="space-y-6">
            {% csrf_token %}
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Item Name *</label>
                <input type="text" name="name" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea name="description" rows="3" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"></textarea>
            </div>
            
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Price *</label>
                    <input type="number" name="price" step="0.01" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Category *</label>
                    <select name="category" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
                        <option value="">Select Category</option>
                        <option value="breakfast">Breakfast</option>
                        <option value="lunch">Lunch</option>
                        <option value="dinner">Dinner</option>
                        <option value="snacks">Snacks</option>
                        <option value="beverages">Beverages</option>
                    </select>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Image</label>
                <input type="file" name="image" accept="image/*" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
            </div>
            
            <div class="flex items-center">
                <input type="checkbox" name="is_available" id="is_available" checked class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary">
                <label for="is_available" class="ml-2 text-sm text-gray-700">Available</label>
            </div>
            
            <div class="flex space-x-4 pt-4">
                <button type="submit" class="px-8 py-3 gradient-bg text-white rounded-lg font-medium hover:shadow-lg smooth-transition">
                    <i class="fas fa-save mr-2"></i>Add Menu Item
                </button>
                <a href="{% url 'admin_menu_list' %}" class="px-8 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 smooth-transition">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''',
    
    'menu_edit.html': '''{% extends 'admin_portal/layout.html' %}

{% block title %}Edit Menu Item - UAP Admin{% endblock %}

{% block content %}
<div class="max-w-3xl">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h3 class="text-2xl font-bold text-primary mb-6">Edit Menu Item</h3>
        
        <form method="POST" enctype="multipart/form-data" class="space-y-6">
            {% csrf_token %}
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Item Name *</label>
                <input type="text" name="name" value="{{ item.name }}" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea name="description" rows="3" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">{{ item.description }}</textarea>
            </div>
            
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Price *</label>
                    <input type="number" name="price" value="{{ item.price }}" step="0.01" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Category *</label>
                    <select name="category" required class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
                        <option value="breakfast" {% if item.category == 'breakfast' %}selected{% endif %}>Breakfast</option>
                        <option value="lunch" {% if item.category == 'lunch' %}selected{% endif %}>Lunch</option>
                        <option value="dinner" {% if item.category == 'dinner' %}selected{% endif %}>Dinner</option>
                        <option value="snacks" {% if item.category == 'snacks' %}selected{% endif %}>Snacks</option>
                        <option value="beverages" {% if item.category == 'beverages' %}selected{% endif %}>Beverages</option>
                    </select>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Image</label>
                {% if item.image %}
                <img src="{{ item.image.url }}" alt="{{ item.name }}" class="w-32 h-32 object-cover rounded-lg mb-2">
                {% endif %}
                <input type="file" name="image" accept="image/*" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition">
            </div>
            
            <div class="flex items-center">
                <input type="checkbox" name="is_available" id="is_available" {% if item.is_available %}checked{% endif %} class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary">
                <label for="is_available" class="ml-2 text-sm text-gray-700">Available</label>
            </div>
            
            <div class="flex space-x-4 pt-4">
                <button type="submit" class="px-8 py-3 gradient-bg text-white rounded-lg font-medium hover:shadow-lg smooth-transition">
                    <i class="fas fa-save mr-2"></i>Update Menu Item
                </button>
                <a href="{% url 'admin_menu_list' %}" class="px-8 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 smooth-transition">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
'''
}

for filename, content in templates.items():
    with open(f'/Users/sultanarupa/Documents/lab-project/uap-smartcampus-demo/templates/admin_portal/{filename}', 'w') as f:
        f.write(content)
    print(f'Created {filename}')

print('Done!')
