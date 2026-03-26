import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const statusBadge = (status) => {
    const base = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold tracking-wide';
    switch (status) {
        case 'AVAILABLE':
            return `${base} bg-emerald-100 text-emerald-700 border border-emerald-200`;
        case 'IN USE':
            return `${base} bg-amber-100 text-amber-700 border border-amber-200`;
        default:
            return `${base} bg-slate-100 text-slate-700 border border-slate-200`;
    }
};

const StatCard = ({ title, value, accent }) => (
    <div className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm p-4">
        <div className={`absolute inset-x-0 top-0 h-1 ${accent}`} />
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-3xl font-extrabold text-gray-900 mt-1">{value}</p>
    </div>
);

const navItems = [
    { id: 'inventory', label: 'Inventory', icon: '📦', blurb: 'All stock and components', section: 'Inventory' },
    { id: 'builds', label: 'Build Planner', icon: '🛠️', blurb: 'Draft and track PC builds', section: 'Planning' },
    { id: 'autobuilder', label: 'Auto-Builder', icon: '🤖', blurb: 'Auto-detect buildable combos', section: 'Planning' },
    { id: 'picker', label: 'PC Part Picker', icon: '🧮', blurb: 'Cost out potential builds', section: 'Planning' },
    { id: 'prebuilts', label: 'Pre-Builts', icon: '🏗️', blurb: 'Spec planned builds with external sourcing', section: 'Planning' },
    { id: 'shortages', label: 'Shortages', icon: '🚨', blurb: 'See what parts block builds', section: 'Supply' },
    { id: 'suppliers', label: 'Suppliers', icon: '🤝', blurb: 'Vendors, pricing, contacts', section: 'Supply' },
    { id: 'orders', label: 'Orders', icon: '🧾', blurb: 'Quotes, invoices, sales', section: 'Supply' },
    { id: 'sales', label: 'Sales', icon: '💼', blurb: 'Deals, invoices, pipeline', section: 'Business' },
    { id: 'ops', label: 'Ops & Profit', icon: '📈', blurb: 'Orders + sales + profit view', section: 'Business' },
    { id: 'profit', label: 'Profit Engine', icon: '🔥', blurb: 'Capital, ROI, best moves', section: 'Business' },
    { id: 'finance', label: 'Financial Planner', icon: '💹', blurb: 'Business budgets & projections', section: 'Business' },
    { id: 'tasks', label: 'Tasks', icon: '✅', blurb: 'Follow-ups and reminders', section: 'Actions' },
    { id: 'about', label: 'About', icon: 'ℹ️', blurb: 'WhatAPC vision & strategy', section: 'Info' },
    { id: 'links', label: 'Social & Links', icon: '🔗', blurb: 'Quick links to socials, stores, pages', section: 'Info' }
];

const InventoryList = () => {
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [itemTypeFilter, setItemTypeFilter] = useState('');
    const [brandFilter, setBrandFilter] = useState('');
    const [lowOnly, setLowOnly] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [sortField, setSortField] = useState('inventory_id');
    const [sortOrder, setSortOrder] = useState('asc');
    const [selectedItems, setSelectedItems] = useState([]);
    const [bulkAction, setBulkAction] = useState('');
    const [stats, setStats] = useState({ total: 0, available: 0, inUse: 0, lowStock: 0 });
    const [formData, setFormData] = useState({
        inventory_id: '',
        item_type: '',
        brand: '',
        model: '',
        component: '',
        qty: 1,
        details: '',
        socket_or_interface: '',
        status: 'AVAILABLE',
        used_in: '',
        ownership: 'INVENTORY',
        test_status: 'UNTESTED',
        cooler_required: '',
        notes: '',
        photo_refs: '',
        price_paid: '',
        source: '',
        seller: '',
        location_bin: '',
        location_shelf: '',
        location_notes: ''
    });
    const [showForm, setShowForm] = useState(false);
    const [editingItem, setEditingItem] = useState(null);
    const [modalAnchor, setModalAnchor] = useState({ top: '50%', left: '50%' });
    const [importFile, setImportFile] = useState(null);
    const defaultThreshold = 1;
    const [thresholds, setThresholds] = useState({
        'cpu cooler': 1,
        cooler: 1,
        fan: 1,
        'case fan': 1,
        'thermal paste': 1
    });
    const [thresholdModal, setThresholdModal] = useState(false);
    const [newThreshold, setNewThreshold] = useState({ type: '', value: 1 });
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [activePage, setActivePage] = useState('inventory');
    const [fullInventory, setFullInventory] = useState([]);
    const [builds, setBuilds] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('buildPlans')) || [];
        } catch (_) {
            return [];
        }
    });
    const [buildForm, setBuildForm] = useState({
        id: null,
        name: '',
        client: '',
        budget: '',
        priority: 'Normal',
        due_date: '',
        status: 'Draft',
        notes: '',
        parts: []
    });
    const [partSelection, setPartSelection] = useState({ inventory_id: '', qty: 1 });
    const [partPicker, setPartPicker] = useState({ category: '', filtered: [] });
    const [tasks, setTasks] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('tasks')) || [];
        } catch (_) {
            return [];
        }
    });
    const [suppliers, setSuppliers] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('suppliers')) || [];
        } catch (_) {
            return [];
        }
    });
    const [orders, setOrders] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('orders')) || [];
        } catch (_) {
            return [];
        }
    });
    const [reservations, setReservations] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('reservations')) || [];
        } catch (_) {
            return [];
        }
    });
    const [notifications, setNotifications] = useState([]);
    const [priceHistory, setPriceHistory] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('priceHistory')) || {};
        } catch (_) {
            return {};
        }
    });
    const latestPrice = useCallback((invId) => {
        const arr = priceHistory[invId] || [];
        if (arr.length > 0) return arr[arr.length - 1];
        const item = fullInventory.find((i) => i.inventory_id === invId);
        return Number(item?.price_paid) || 0;
    }, [priceHistory, fullInventory]);

    const costForParts = useCallback(
        (parts = []) =>
            parts.reduce((sum, p) => {
                const qty = p.qty || 1;
                return sum + latestPrice(p.inventory_id) * qty;
            }, 0),
        [latestPrice]
    );
    // changeLog removed (unused)
    const [deals, setDeals] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('deals')) || [];
        } catch (_) {
            return [];
        }
    });
    const [dealForm, setDealForm] = useState({
        id: null,
        name: '',
        client: '',
        buildId: '',
        amount: '',
        stage: 'Lead',
        status: 'Open',
        due_date: '',
        notes: ''
    });
    const [helpOpen, setHelpOpen] = useState(false);
    const [toastState, setToastState] = useState({ message: '', success: true, visible: false });
    const [opsRange, setOpsRange] = useState('all'); // all | 30 | 90 days
    const thresholdList = useMemo(() => {
        const baseTypes = [
            'CPU',
            'GPU',
            'MOTHERBOARD',
            'RAM',
            'PSU',
            'CASE',
            'CPU COOLER',
            'FAN',
            'STORAGE',
            'SSD',
            'HDD',
            'GPU COOLER',
            'NETWORKING',
            'ROUTER',
            'SWITCH',
            'NIC',
            'OS',
            'PSU CABLE',
            'KEYBOARD',
            'MICE',
            'MONITOR',
            'HEADSET'
        ];
        return Array.from(new Set([...Object.keys(thresholds), ...baseTypes]))
            .filter(Boolean)
            .sort();
    }, [thresholds]);
    const [preBuilts, setPreBuilts] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('preBuilts')) || [];
        } catch (_) {
            return [];
        }
    });
    const [preBuiltForm, setPreBuiltForm] = useState({
        id: null,
        name: '',
        tier: '',
        targetUse: '',
        targetSell: '',
        taxPercent: 0,
        notes: '',
        parts: []
    });
    const [prePart, setPrePart] = useState({
        name: '',
        category: '',
        link: '',
        vendor: '',
        cost: '',
        shippingDays: '',
        qty: 1,
        condition: '',
        sku: '',
        notes: '',
        tax: '',
        shipCost: ''
    });

    const helpCopy = {
        inventory: [
            'Purpose: Central hub to view, filter, import/export, and edit inventory.',
            'Top bar: Add New Item opens the item form; Export CSV downloads current filtered view; Low-stock rules sets custom thresholds; Re-run normalization re-applies type/socket/DDR detection.',
            'Filters: Search (brand/model/details), Status, Type, Brand, Low-stock only, Dark/Light toggle.',
            'Type overview: Groups items by category with low badges; click a type to expand models; click a model to open the detail modal.',
            'Detail modal: Shows normalized socket/DDR/TD P etc., with Edit inline and Edit button.',
            'Thresholds: Custom per-type minimums drive Low Stock badge, shortages, and alerts (now allow 0).',
            'Normalization: CPU/GPU/Case/Cooler/Fan/Storage detection plus sockets, DDR, TDP, PCIe pins/cables, length, age.',
            'Reservations: Quantities reserved for builds are excluded from available counts and low-stock totals.'
        ].join('\n• '),
        builds: [
            'Purpose: Plan builds, check compatibility, reserve parts, export BOM.',
            'Add parts: Select inventory items and qty, save to build. Missing storage/case/cooler/fan are flagged.',
            'Compatibility: Validates socket, DDR, RAM speed/channels, PSU watt/rails/pins, case GPU length, storage present, cooler/fan present.',
            'Shortages widget: Shows blockers for this build; reserve parts to hold stock.',
            'Exports: BOM CSV/PDF; margin shown using price history; compatibility score.',
            'Reservations: Reserve button reduces available stock elsewhere.'
        ].join('\n• '),
        shortages: [
            'Purpose: Shows blockers for builds and inferred gaps (CPU/mobo/RAM + required GPU/Case/Cooler/Fan/Storage/PSU).',
            'Columns: Needed, Available (after reservations), Missing, Builds impacted, Alternates.',
            'Actions: Task (log in Tasks), Order (mark ordered), Prefill PO (draft order), Go to Orders/Suppliers.',
            'Compatibility gaps: Also listed below when CPUs lack matching mobos/RAM or essentials are missing.'
        ].join('\n• '),
        picker: [
            'Purpose: Quick financial quotes without tying to inventory.',
            'Add parts with costs, set sell price, see profit and margin; export quote CSV.',
            'Use for “what-if” pricing when parts aren’t in inventory yet.'
        ].join('\n• '),
        autobuilder: [
            'Purpose: Auto-detect buildable combos from available inventory.',
            'Complete builds: CPU+MB+RAM+PSU+Storage+Case+Cooler+Fan (GPU optional) with compatibility score and BOM export.',
            'Partial builds: Lists missing parts; use needs list to order or pick substitutes.'
        ].join('\n• '),
        suppliers: [
            'Purpose: Store vendors with channel, contact, preferred items, and notes.',
            'SLA: Orders vs delivered auto-computes SLA%; list sorted by SLA to pick best supplier.',
            'Use in shortages/orders to recommend where to buy.'
        ].join('\n• '),
        orders: [
            'Purpose: Track purchases/quotes with status, totals, ETA, tracking, and line items.',
            'Prefill PO: from shortages; edit vendor/channel/status/total/due/tracking/items/notes.',
            'Use status Delivered to feed SLA and spend stats.'
        ].join('\n• '),
        sales: [
            'Purpose: Deals pipeline; link builds, set sell price, track stage and status.',
            'Margin: Uses linked build cost (price history) for margin warning.',
            'Exports: Invoice PDF; edit/clear/save deals.'
        ].join('\n• '),
        ops: [
            'Purpose: Combined view of orders + sales + shortages; shows spend, delivered spend, closed-deal revenue/margin, what-to-order list.',
            'What to order: Combines shortages and low-type gaps; suggests best supplier by SLA.',
            'Profit quick look: Margins per deal; use to decide next purchase/sale actions.'
        ].join('\n• '),
        finance: 'Purpose: Monthly revenue/expense planner; add months with revenue/expenses/notes for budgeting.',
        tasks: 'Purpose: Action inbox. Restock/ordered buttons from Shortages land here; track status, priority, and due dates.',
        about: 'Strategy/vision: Forever PC philosophy, supply model, services, legal, digital roadmap, timeline.',
        links: 'Quick-launch: store your Facebook/eBay/links with notes; open/edit/delete quickly.',
        profit: [
            'Purpose: Decision brain for ROI and capital velocity.',
            'True cost: price + inbound/outbound/platform fees + labor (track even if $0).',
            'Market estimate: low/mid/high via condition multiplier; demand class HOT/NORMAL/SLOW.',
            'Metrics: gross profit, ROI%, profit/day, capital velocity; shows best build to assemble now.',
            'Top items: highest profit/day; decision cues for build/hold/part-out.'
        ].join('\n• ')
    };
    const inRange = useCallback(
        (dateStr) => {
            if (opsRange === 'all') return true;
            if (!dateStr) return true;
            const d = new Date(dateStr);
            if (Number.isNaN(d.getTime())) return true;
            const days = opsRange === '30' ? 30 : 90;
            const diff = (Date.now() - d.getTime()) / (1000 * 60 * 60 * 24);
            return diff <= days;
        },
        [opsRange]
    );

    const opsStats = useMemo(() => {
        const filteredOrders = orders.filter((o) => inRange(o.created_at || o.due_date));
        const filteredDeals = deals.filter((d) => inRange(d.due_date));
        const orderSpend = filteredOrders.reduce((sum, o) => sum + (Number(o.total) || 0), 0);
        const deliveredSpend = filteredOrders.filter((o) => o.status === 'Delivered').reduce((sum, o) => sum + (Number(o.total) || 0), 0);
        const closedDeals = filteredDeals.filter((d) => d.stage === 'Won' || d.status === 'Closed');
        const dealRevenue = closedDeals.reduce((sum, d) => sum + (Number(d.amount) || 0), 0);
        const dealMargin = (() => {
            let numerator = 0;
            let denom = 0;
            closedDeals.forEach((d) => {
                const build = builds.find((b) => b.id === d.buildId);
                const partsArr = build?.parts || [];
                const cost = costForParts(partsArr);
                const sell = Number(d.amount || 0);
                if (sell) {
                    numerator += sell - cost;
                    denom += sell;
                }
            });
            return denom ? Math.round((numerator / denom) * 100) : 0;
        })();
        return { orderSpend, deliveredSpend, dealRevenue, dealMargin };
    }, [orders, deals, builds, costForParts, inRange]);

    const [autoFilters, setAutoFilters] = useState({ socket: '', ddr: '', minPsu: 0 });
    const [taskForm, setTaskForm] = useState({
        id: null,
        title: '',
        category: 'General',
        status: 'Open',
        priority: 'Normal',
        due_date: '',
        notes: ''
    });
    const [expandedType, setExpandedType] = useState(null);
    const [detailItem, setDetailItem] = useState(null);
    const [financialBuilds, setFinancialBuilds] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('financialPlans')) || [];
        } catch (_) {
            return [];
        }
    });
    const [financialForm, setFinancialForm] = useState({
        id: null,
        name: '',
        parts: [],
        sellPrice: ''
    });
    const [finPart, setFinPart] = useState({ name: '', type: '', link: '', cost: '' });
    const [bizPlans, setBizPlans] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('businessPlans')) || [];
        } catch (_) {
            return [];
        }
    });
    const [bizForm, setBizForm] = useState({
        id: null,
        month: '',
        revenue: '',
        expenses: '',
        notes: ''
    });
    const [socialLinks, setSocialLinks] = useState(() => {
        try {
            return (
                JSON.parse(localStorage.getItem('socialLinks')) || [
                    { id: 'fb', label: 'Facebook', url: 'https://www.facebook.com/profile.php?id=61559722659541', note: 'Business page' },
                    { id: 'ebay', label: 'eBay', url: 'https://www.ebay.com/', note: '' }
                ]
            );
        } catch (_) {
            return [];
        }
    });
    const [socialForm, setSocialForm] = useState({ id: null, label: '', url: '', note: '' });
    const [theme, setTheme] = useState('light');
    const [orderForm, setOrderForm] = useState({
        id: null,
        vendor: '',
        channel: '',
        status: 'Draft',
        total: '',
        due_date: '',
        tracking: '',
        items: '',
        notes: ''
    });
    const [supplierForm, setSupplierForm] = useState({
        name: '',
        contact: '',
        channel: '',
        website: '',
        notes: '',
        preferred_items: ''
    });

    const thresholdFor = useCallback(
        (type) => {
            const key = (type || '').toLowerCase().trim();
            if (Object.prototype.hasOwnProperty.call(thresholds, key)) {
                const v = Number(thresholds[key]);
                return Number.isFinite(v) ? v : defaultThreshold;
            }
            return defaultThreshold;
        },
        [thresholds, defaultThreshold]
    );

    const normalizeType = (item) => {
        const blob = `${item.item_type || ''} ${item.component || ''} ${item.model || ''} ${item.details || ''}`.toLowerCase();
        const cpuRegex = /(core\s+i[3579])|(i[3579]-\d{3,5})|(ryzen)|(xeon)|(athlon)|(threadripper)|(epyc)|(pentium)|(celeron)|(fx-\d)|(g\d{3,4})/;
        const gpuRegex = /(rtx|gtx|rx\s?\d{3,4}|quadro|geforce|radeon|graphics\s*card|gpu)/;
        const ramRegex = /\bram\b|\bddr\d\b|\bso-dimm\b|\bdimm\b/;
        const psuRegex = /(psu|power\s*supply|atx\s*\d{3,4}w|\d{3,4}w\s*psu)/;
        const caseFanRegex = /case\s*fan/;
        const caseRegex = /\b(pc\s*)?case\b|mid\s*tower|full\s*tower|micro\s*atx\s*tower|itx\s*tower|atx\s*tower/;
        const kbRegex = /(keyboard|key\s*board|kb\b)/;
        const mouseRegex = /(mouse|mice)/;
        const coolerRegex = /(cpu\s*cooler|cooler|heatsink|heat\s*sink|aio|liquid\s*cool|water\s*cool|radiator)/;
        const fanRegex = /\bfan(s)?\b|120mm|140mm|92mm|80mm/;
        const osRegex = /(windows\s*(10|11)|win10|win11|license|product\s*key|os\b)/;
        const cableRegex = /(psu\s*cable|pcie\s*cable|gpu\s*cable|8-?pin\s*cable|6-?pin\s*cable)/;
        if (/pc\s*combo|combo/.test(blob) && cpuRegex.test(blob)) return 'PC COMBO';

        if (kbRegex.test(blob) && mouseRegex.test(blob)) return 'KEYBOARD/MOUSE COMBO';
        if (kbRegex.test(blob)) return 'KEYBOARD';
        if (mouseRegex.test(blob)) return 'MICE';
        if (cpuRegex.test(blob)) return 'CPU';
        if (gpuRegex.test(blob)) return 'GPU';
        if (ramRegex.test(blob)) return 'RAM';
        if (psuRegex.test(blob)) return 'PSU';
        if (osRegex.test(blob)) return 'OS';
        if (cableRegex.test(blob)) return 'PSU CABLE';
        if (caseFanRegex.test(blob)) return 'FAN';
        if (coolerRegex.test(blob)) return 'CPU COOLER';
        if (caseRegex.test(blob)) return 'CASE';
        if (fanRegex.test(blob)) return 'FAN';
        return (item.item_type || '').toUpperCase() || 'OTHER';
    };

    const deriveStorageSubtype = (item) => {
        const txt = `${item.model || ''} ${item.details || ''} ${item.component || ''}`.toUpperCase();
        if (/NVME|NVME|M\.2/.test(txt)) return 'NVMe';
        if (/SSD/.test(txt)) return 'SSD';
        if (/HDD|RPM/.test(txt)) return 'HDD';
        if (/USB/.test(txt)) return 'USB';
        if (/SATA/.test(txt)) return 'SATA';
        return 'Other';
    };

    const deriveSocket = (item) => {
        const text = `${item.socket_or_interface || ''} ${item.details || ''} ${item.model || ''}`.toUpperCase();
        const socketList = [
            'LGA1851', 'LGA1700', 'LGA1200', 'LGA1151', 'LGA1150', 'LGA1155', 'LGA1156', 'LGA2066', 'LGA2011-3', 'LGA2011', 'LGA1366',
            'LGA1356', 'LGA775', 'LGA771', 'LGA3647', 'LGA4189', 'LGA4677', 'AM5', 'AM4', 'AM3+', 'AM3', 'AM2+', 'AM2', 'FM2+', 'FM2', 'FM1',
            'TR4', 'STRX4', 'SP3', 'SP5', 'sTRX4', 'G34', '939', '940'
        ];
        const matches = socketList.filter((s) => text.includes(s));
        if (matches.length > 0) return Array.from(new Set(matches)).join(' / ');
        const generic = text.match(/(SOCKET\s*[A-Z0-9+]+|LGA\s*\d{3,4}|AM\d|FM\d|\bSP\d\b)/);
        if (generic) return generic[0].replace('SOCKET', '').trim();
        return item.socket_or_interface || '';
    };

    const deriveDdrType = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const match = txt.match(/DDR\d/);
        return match ? match[0] : '';
    };

    const deriveRamSpeed = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const match = txt.match(/(\d{3,4})\s*MHZ/);
        return match ? Number(match[1]) : 0;
    };

    const deriveChannels = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        if (/QUAD\s*CHANNEL/.test(txt)) return 4;
        if (/TRIPLE\s*CHANNEL/.test(txt)) return 3;
        if (/DUAL\s*CHANNEL/.test(txt)) return 2;
        return 0;
    };

    const gpuConnectors = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const matches = txt.match(/(\d+)X\s*8-?PIN|(\d+)X\s*6-?PIN|8-?PIN|6-?PIN/g) || [];
        let count = 0;
        matches.forEach((m) => {
            if (m.includes('X')) {
                const n = parseInt(m, 10) || 1;
                count += n;
            } else {
                count += 1;
            }
        });
        return count;
    };

    const psuConnectors = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const m = txt.match(/(\d+)\s*(PCI[E]?\s*8-?PIN|8-?PIN\s*PCI[E]?)/);
        return m ? Number(m[1]) : 0;
    };

    const parseLengthMm = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const m = txt.match(/(\d{2,4})\s*MM/);
        return m ? Number(m[1]) : 0;
    };

    const parseCaseGpuMax = (item) => {
        const txt = `${item.details || ''}`.toUpperCase();
        const m = txt.match(/GPU\s*MAX\s*LENGTH\s*(\d{2,4})\s*MM|(\d{2,4})\s*MM\s*GPU\s*MAX/);
        return m ? Number(m[1] || m[2]) : 0;
    };

    const deriveAgeDays = (item) => {
        if (!item.purchase_date) return null;
        const d = new Date(item.purchase_date);
        if (isNaN(d.getTime())) return null;
        return Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24));
    };

    const deriveTdpWatts = (item) => {
        const txt = `${item.details || ''} ${item.model || ''}`.toUpperCase();
        const tdpMatch = txt.match(/(\d+)\s*(W|TDP)/);
        if (tdpMatch) return Number(tdpMatch[1]);
        return 0;
    };

    const fetchInventory = useCallback(async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://localhost:5000/api/inventory', {
                params: { search, status: statusFilter, per_page: 1000, sort: sortField, order: sortOrder }
            });
            const processed = response.data.items.map((item) => {
                const normType = normalizeType(item);
                const fixedType = normType === 'MOUSE' ? 'MICE' : normType;
                return {
                    ...item,
                    typeNormalized: fixedType,
                    socketNormalized: deriveSocket(item),
                storageSubtype: fixedType === 'STORAGE' ? deriveStorageSubtype(item) : '',
                    ddrType: deriveDdrType(item),
                    tdp: deriveTdpWatts(item),
                    ramSpeed: deriveRamSpeed(item),
                    channels: deriveChannels(item),
                    pciePins: gpuConnectors(item),
                    pcieCables: psuConnectors(item),
                    lengthMm: parseLengthMm(item),
                    ageDays: deriveAgeDays(item),
                    caseGpuMax: parseCaseGpuMax(item)
                };
            });
            setInventory(processed);
        } catch (error) {
            console.error(error);
        }
        setLoading(false);
    }, [search, sortField, sortOrder, statusFilter]);

    const syncNormalizedTypes = async (items) => {
        try {
            const mismatches = items.filter(
                (i) =>
                    i.item_type !== i.typeNormalized ||
                    (i.socketNormalized && i.socket_type !== i.socketNormalized) ||
                    (i.storageSubtype && i.storage_type !== i.storageSubtype) ||
                    (i.ddrType && i.ddr_type !== i.ddrType) ||
                    (i.tdp && i.tdp_watts !== i.tdp) ||
                    (i.ramSpeed && i.ram_speed_mhz !== i.ramSpeed) ||
                    (i.channels && i.memory_channels !== i.channels) ||
                    (i.pciePins && i.gpu_pcie_pins !== i.pciePins) ||
                    (i.pcieCables && i.psu_pcie_cables !== i.pcieCables) ||
                    (i.lengthMm && i.length_mm !== i.lengthMm)
            );
            if (mismatches.length === 0) return;
            await Promise.all(
                mismatches.map((i) =>
                    axios.put(`http://localhost:5000/api/inventory/${i.id}`, {
                        item_type: i.typeNormalized,
                        socket_type: i.socketNormalized,
                        storage_type: i.storageSubtype,
                        ddr_type: i.ddrType,
                        tdp_watts: i.tdp,
                        ram_speed_mhz: i.ramSpeed,
                        memory_channels: i.channels,
                        gpu_pcie_pins: i.pciePins,
                        psu_pcie_cables: i.pcieCables,
                        length_mm: i.lengthMm
                    })
                )
            );
            toast('Normalization complete', true);
        } catch (error) {
            console.error('Failed to sync normalized types', error);
            toast('Normalization failed', false);
        }
    };

    const fetchStats = useCallback(async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/inventory', { params: { per_page: 1000 } });
            const allItems = response.data.items.map((item) => ({
                ...item,
                typeNormalized: normalizeType(item),
                socketNormalized: deriveSocket(item),
                storageSubtype: normalizeType(item) === 'STORAGE' ? deriveStorageSubtype(item) : '',
                ddrType: deriveDdrType(item),
                tdp: deriveTdpWatts(item),
                ramSpeed: deriveRamSpeed(item),
                channels: deriveChannels(item),
                pciePins: gpuConnectors(item),
                pcieCables: psuConnectors(item),
                lengthMm: parseLengthMm(item),
                ageDays: deriveAgeDays(item),
                caseGpuMax: parseCaseGpuMax(item)
            }));
            const total = allItems.length;
            const available = allItems.filter((item) => item.status === 'AVAILABLE').length;
            const inUse = allItems.filter((item) => item.status === 'IN USE').length;
            const baseTypes = [
                'CPU',
                'GPU',
                'MOTHERBOARD',
                'RAM',
                'PSU',
                'CASE',
                'CPU COOLER',
                'FAN',
                'STORAGE',
                'SSD',
                'HDD',
                'GPU COOLER',
                'NETWORKING',
                'ROUTER',
                'SWITCH',
                'NIC',
                'KEYBOARD',
                'MICE',
                'MONITOR',
                'HEADSET'
            ];
            const typeTotals = {};
            allItems.forEach((item) => {
                const key = item.typeNormalized || 'OTHER';
                const reservedQty = reservations
                    .filter((r) => r.inventory_id === item.inventory_id)
                    .reduce((s, r) => s + (r.qty || 0), 0);
                const availQty = Math.max(0, (Number(item.qty) || 0) - reservedQty);
                typeTotals[key] = (typeTotals[key] || 0) + availQty;
            });
            // ensure base types exist with zero
            baseTypes.forEach((t) => {
                if (!(t in typeTotals)) typeTotals[t] = 0;
            });
            const lowStock = Object.entries(typeTotals).reduce((count, [t, qty]) => {
                return count + (qty < thresholdFor(t) ? 1 : 0);
            }, 0);
            setStats({ total, available, inUse, lowStock });
            setFullInventory(allItems);
            // update price history
            setPriceHistory((prev) => {
                const next = { ...prev };
                allItems.forEach((it) => {
                    if (!it.inventory_id) return;
                    const paid = Number(it.price_paid);
                    if (!paid) return;
                    const arr = next[it.inventory_id] || [];
                    if (arr.length === 0 || arr[arr.length - 1] !== paid) {
                        arr.push(paid);
                        next[it.inventory_id] = arr.slice(-5);
                    }
                });
                return next;
            });

            // simple change log placeholder (manual add later)
            await syncNormalizedTypes(allItems);
        } catch (error) {
            console.error(error);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [thresholdFor]);


    const filteredInventory = useMemo(() => {
        return inventory
            .filter((item) => (itemTypeFilter ? item.typeNormalized === itemTypeFilter : true))
            .filter((item) => (brandFilter ? item.brand === brandFilter : true))
            .filter((item) => (lowOnly ? item.qty < thresholdFor(item.typeNormalized) : true));
    }, [inventory, itemTypeFilter, brandFilter, lowOnly, thresholdFor]);

    const pageSize = 10;
    const pageItems = useMemo(() => {
        const start = (page - 1) * pageSize;
        return filteredInventory.slice(start, start + pageSize);
    }, [filteredInventory, page]);

    const groupForType = (type) => {
        const t = (type || '').toUpperCase();
        const components = ['CPU', 'GPU', 'MOTHERBOARD', 'RAM', 'STORAGE', 'SSD', 'HDD', 'PSU', 'POWER SUPPLY', 'CASE', 'CPU COOLER', 'FAN', 'HEATSINK', 'GPU COOLER', 'PCIe CARD'];
        const networking = ['ROUTER', 'SWITCH', 'NIC', 'NETWORK', 'ACCESS POINT', 'AP', 'MODEM', 'FIREWALL'];
        const peripherals = ['KEYBOARD', 'MICE', 'KEYBOARD/MOUSE COMBO', 'MONITOR', 'WEBCAM', 'HEADSET', 'HEADPHONE', 'HEADPHONES', 'EARBUD', 'EARBUDS', 'MIC', 'SPEAKER'];
        const tools = ['TOOL', 'CABLE', 'ADAPTER', 'TESTER', 'THERMAL PASTE', 'PASTE', 'SCREW', 'BRACKET'];
        if (components.some((c) => t.includes(c))) return 'Components';
        if (networking.some((c) => t.includes(c))) return 'Networking';
        if (peripherals.some((c) => t.includes(c))) return 'Peripherals';
        if (tools.some((c) => t.includes(c))) return 'Tools';
        return 'Other';
    };

    const groupedOverview = useMemo(() => {
        const baseGroups = {
            Components: ['CPU', 'GPU', 'MOTHERBOARD', 'RAM', 'PSU', 'CASE', 'CPU COOLER', 'FAN', 'STORAGE', 'SSD', 'HDD', 'GPU COOLER'],
            Networking: ['ROUTER', 'SWITCH', 'NIC', 'NETWORKING', 'ACCESS POINT', 'MODEM'],
            Peripherals: ['KEYBOARD', 'MICE', 'KEYBOARD/MOUSE COMBO', 'MONITOR', 'HEADSET', 'SPEAKER', 'WEBCAM'],
            Tools: ['THERMAL PASTE', 'ADAPTER', 'CABLE', 'TESTER', 'TOOL'],
            Other: ['OTHER']
        };
        const acc = {};
        // seed base groups with zero counts/qty
        Object.entries(baseGroups).forEach(([group, types]) => {
            acc[group] = acc[group] || {};
            types.forEach((t) => {
                acc[group][t] = { count: 0, qty: 0, low: 0 };
            });
        });
        fullInventory.forEach((item) => {
            const g = groupForType(item.typeNormalized);
            acc[g] = acc[g] || {};
            const key = item.typeNormalized || 'OTHER';
            const reservedQty = reservations
                .filter((r) => r.inventory_id === item.inventory_id)
                .reduce((s, r) => s + (r.qty || 0), 0);
            const avail = Math.max(0, (Number(item.qty) || 0) - reservedQty);
            acc[g][key] = acc[g][key] || { count: 0, qty: 0, low: 0 };
            acc[g][key].count += 1;
            acc[g][key].qty += avail;
        });
        // compute low based on total qty vs threshold
        Object.entries(acc).forEach(([, types]) => {
            Object.entries(types).forEach(([typeKey, info]) => {
                const need = Math.max(0, thresholdFor(typeKey) - info.qty);
                info.low = need;
            });
        });
        return acc;
    }, [fullInventory, thresholdFor, reservations]);

    const autoBuilds = useMemo(() => {
        const avail = fullInventory.filter((i) => i.status === 'AVAILABLE' && Number(i.qty) > 0);
        const cpus = avail.filter((i) => i.typeNormalized === 'CPU');
        const mobos = avail.filter((i) => i.typeNormalized === 'MOTHERBOARD');
        const rams = avail.filter((i) => i.typeNormalized === 'RAM');
        const psus = avail.filter((i) => i.typeNormalized === 'PSU' || i.typeNormalized === 'POWER SUPPLY');
        const gpus = avail.filter((i) => i.typeNormalized === 'GPU');
        const cases = avail.filter((i) => i.typeNormalized === 'CASE');
        const coolers = avail.filter((i) => i.typeNormalized === 'CPU COOLER');
        const storages = avail.filter((i) => ['STORAGE', 'SSD', 'HDD'].includes(i.typeNormalized));
        const caseFans = avail.filter((i) => i.typeNormalized === 'FAN');

        const combos = [];
        const partials = [];

        cpus.forEach((cpu) => {
            if (autoFilters.socket && cpu.socketNormalized && cpu.socketNormalized !== autoFilters.socket) return;
            const mbMatch = mobos.find((m) => m.socketNormalized && m.socketNormalized === cpu.socketNormalized);
            const mbDdr = mbMatch?.ddrType;
            const ramMatch = rams.find((r) => (!mbDdr || !r.ddrType || r.ddrType === mbDdr));
            const psuMatch = psus.find((p) => {
                if (autoFilters.minPsu) {
                    const watts = Number(p.details?.match(/(\d+)\s*w/i)?.[1]) || 0;
                    return watts >= autoFilters.minPsu;
                }
                return true;
            });
            const gpuMatch = gpus[0] || null;
            const caseMatch = cases[0] || null;
            const coolerMatch = coolers[0] || null;
            const storageMatch = storages[0] || null;
            const fanMatch = caseFans[0] || null;

            const missing = [];
            if (!mbMatch) missing.push('Motherboard');
            if (!ramMatch) missing.push(`RAM${mbDdr ? ` (${mbDdr})` : ''}`);
            if (!psuMatch) missing.push('PSU');
            if (!storageMatch) missing.push('Storage (HDD/SSD/NVMe)');
            if (!caseMatch) missing.push('Case');
            if (!coolerMatch) missing.push('CPU Cooler');
            if (!fanMatch) missing.push('Case fan');

            if (missing.length === 0) {
                combos.push({
                    id: `${cpu.inventory_id}-${mbMatch.inventory_id}`,
                    cpu,
                    motherboard: mbMatch,
                    ram: ramMatch,
                    psu: psuMatch,
                    gpu: gpuMatch,
                    case: caseMatch,
                    cooler: coolerMatch,
                    storage: storageMatch,
                    fan: fanMatch,
                    socket: cpu.socketNormalized || mbMatch?.socketNormalized || '—',
                    ddr: mbDdr || ramMatch?.ddrType || '—'
                });
            } else {
                partials.push({
                    id: `${cpu.inventory_id}-partial`,
                    cpu,
                    motherboard: mbMatch,
                    ram: ramMatch,
                    psu: psuMatch,
                    missing
                });
            }
        });

        return {
            complete: combos,
            partial: partials,
            missing: cpus.length === 0 && combos.length === 0 && partials.length === 0 ? ['Need CPU, motherboard, RAM, PSU'] : []
        };
    }, [fullInventory, autoFilters]);

    useEffect(() => {
        const pages = Math.max(1, Math.ceil(filteredInventory.length / pageSize));
        setTotalPages(pages);
        if (page > pages) setPage(1);
    }, [filteredInventory, page]);

    // initial load and sorting/filtering changes
    useEffect(() => {
        const saved = localStorage.getItem('lowStockThresholds');
        if (saved) {
            try {
                setThresholds(JSON.parse(saved));
            } catch (_) {
                /* ignore bad json */
            }
        }
        fetchInventory();
    }, [fetchInventory]);

    // persist thresholds
    useEffect(() => {
        localStorage.setItem('lowStockThresholds', JSON.stringify(thresholds));
        fetchStats();
    }, [thresholds, fetchStats]);

    useEffect(() => {
        localStorage.setItem('buildPlans', JSON.stringify(builds));
    }, [builds]);

    useEffect(() => {
        localStorage.setItem('tasks', JSON.stringify(tasks));
    }, [tasks]);

    useEffect(() => {
        localStorage.setItem('suppliers', JSON.stringify(suppliers));
    }, [suppliers]);

    useEffect(() => {
        localStorage.setItem('orders', JSON.stringify(orders));
    }, [orders]);

    useEffect(() => {
        localStorage.setItem('reservations', JSON.stringify(reservations));
    }, [reservations]);

    useEffect(() => {
        localStorage.setItem('priceHistory', JSON.stringify(priceHistory));
    }, [priceHistory]);

    // changeLog effect removed

    useEffect(() => {
        localStorage.setItem('deals', JSON.stringify(deals));
    }, [deals]);

    useEffect(() => {
        localStorage.setItem('preBuilts', JSON.stringify(preBuilts));
    }, [preBuilts]);

    useEffect(() => {
        localStorage.setItem('financialPlans', JSON.stringify(financialBuilds));
    }, [financialBuilds]);

    useEffect(() => {
        localStorage.setItem('businessPlans', JSON.stringify(bizPlans));
    }, [bizPlans]);

    useEffect(() => {
        localStorage.setItem('socialLinks', JSON.stringify(socialLinks));
    }, [socialLinks]);

    useEffect(() => {
        if (!document.getElementById('dark-filter-style')) {
            const style = document.createElement('style');
            style.id = 'dark-filter-style';
            style.innerHTML = `
            .dark-filter { filter: invert(1) hue-rotate(180deg); background-color:#0b1220!important; }
            .dark-filter img, .dark-filter video { filter: invert(1) hue-rotate(180deg); }
            `;
            document.head.appendChild(style);
        }
        if (theme === 'dark') {
            document.body.classList.add('dark-filter');
        } else {
            document.body.classList.remove('dark-filter');
        }
    }, [theme]);

    useEffect(() => {
        if (showForm) {
            const top = window.scrollY + window.innerHeight / 2;
            setModalAnchor({ top: `${top}px`, left: '50%' });
        }
    }, [showForm]);

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingItem) {
                await axios.put(`http://localhost:5000/api/inventory/${editingItem.id}`, formData);
            } else {
                await axios.post('http://localhost:5000/api/inventory', formData);
            }
            await fetchInventory();
            await fetchStats();
            setShowForm(false);
            setEditingItem(null);
            resetForm();
        } catch (error) {
            console.error(error);
        }
    };

    const handleEdit = (item) => {
        setEditingItem(item);
        setFormData({ ...item });
        setShowForm(true);
    };

    const handleSort = (field) => {
        const order = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(order);
        setPage(1);
    };

    const handleSelectItem = (id) => {
        setSelectedItems((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
    };

    const handleBulkAction = async () => {
        if (!bulkAction || selectedItems.length === 0) return;
        try {
            if (bulkAction === 'delete') {
                await Promise.all(selectedItems.map((id) => axios.delete(`http://localhost:5000/api/inventory/${id}`)));
                alert('Selected items deleted');
            } else if (bulkAction === 'update') {
                await Promise.all(selectedItems.map((id) => axios.put(`http://localhost:5000/api/inventory/${id}`, { status: 'IN USE' })));
                alert('Selected items updated to In Use');
            }
            setSelectedItems([]);
            await fetchInventory();
            await fetchStats();
        } catch (error) {
            console.error(error);
        }
    };

    const exportToCSV = () => {
        const headers = ['inventory_id', 'item_type', 'brand', 'model', 'qty', 'status', 'details'];
        const csvContent = [headers.join(',')]
            .concat(
                inventory.map((item) =>
                    [item.inventory_id, item.item_type, item.brand, item.model, item.qty, item.status, `"${item.details}"`].join(',')
                )
            )
            .join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'inventory_export.csv';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleImport = async (e) => {
        e.preventDefault();
        if (!importFile) return;
        const text = await importFile.text();
        const lines = text.split('\n').filter((line) => line.trim());
        const headers = lines[0].split(',');
        const data = lines.slice(1).map((line) => {
            const values = line.split(',');
            return headers.reduce((obj, header, i) => {
                obj[header.trim()] = values[i]?.trim() || '';
                return obj;
            }, {});
        });
        try {
            await Promise.all(data.map((item) => axios.post('http://localhost:5000/api/inventory', item)));
            alert('Data imported successfully');
            fetchInventory();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this item?')) {
            try {
                await axios.delete(`http://localhost:5000/api/inventory/${id}`);
                await fetchInventory();
                await fetchStats();
            } catch (error) {
                console.error(error);
            }
        }
    };

    const resetForm = () => {
        setFormData({
            inventory_id: '',
            item_type: '',
            brand: '',
            model: '',
            component: '',
            qty: 1,
            details: '',
            socket_or_interface: '',
            status: 'AVAILABLE',
            used_in: '',
            ownership: 'INVENTORY',
            test_status: 'UNTESTED',
            cooler_required: '',
            notes: '',
            photo_refs: '',
            price_paid: '',
            source: '',
            seller: '',
            location_bin: '',
            location_shelf: '',
            location_notes: ''
        });
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleBuildChange = (e) => {
        const { name, value } = e.target;
        setBuildForm((prev) => ({ ...prev, [name]: value }));
    };

    const upsertThreshold = (e) => {
        e.preventDefault();
        if (!newThreshold.type.trim()) return;
        const key = newThreshold.type.toLowerCase().trim();
        const valueNum = Number(newThreshold.value);
        setThresholds((prev) => ({ ...prev, [key]: Number.isFinite(valueNum) ? valueNum : defaultThreshold }));
        setNewThreshold({ type: '', value: defaultThreshold });
        setThresholdModal(false);
    };

    const shortageForPart = (inventory_id, neededQty) => {
        const item = fullInventory.find((i) => i.inventory_id === inventory_id);
        const reservedQty = reservations
            .filter((r) => r.inventory_id === inventory_id)
            .reduce((s, r) => s + (r.qty || 0), 0);
        const available = Math.max(0, (item ? Number(item.qty) || 0 : 0) - reservedQty);
        const missing = Math.max(0, neededQty - available);
        return { available, missing, item };
    };

    const exportBuildCsv = (build) => {
        if (!build?.parts?.length) {
            alert('No parts to export.');
            return;
        }
        const rows = [
            ['Inventory ID', 'Type', 'Brand', 'Model', 'Qty', 'Cost Each', 'Cost Total'],
            ...build.parts.map((p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id) || {};
                const qty = p.qty || 1;
                const cost = Number(item.price_paid) || 0;
                return [p.inventory_id, item.typeNormalized || item.item_type || '', item.brand || '', item.model || '', qty, cost, (cost * qty).toFixed(2)];
            }),
            [],
            ['Total Cost', costForParts(build.parts).toFixed(2)],
            ['Target Sell', build.budget || ''],
            ['Margin %', build.budget ? (((build.budget - costForParts(build.parts)) / build.budget) * 100).toFixed(1) : '']
        ];
        const csv = rows.map((r) => r.map((c) => `"${(c ?? '').toString().replace(/"/g, '""')}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${build.name || 'build'}-bom.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const exportBuildPdf = (build) => {
        if (!build?.parts?.length) {
            alert('No parts to export.');
            return;
        }
        const rows = build.parts.map((p) => {
            const item = fullInventory.find((i) => i.inventory_id === p.inventory_id) || {};
            const qty = p.qty || 1;
            const cost = latestPrice(p.inventory_id);
            return { id: p.inventory_id, type: item.typeNormalized || item.item_type || '', brand: item.brand || '', model: item.model || '', qty, cost, total: (cost * qty).toFixed(2) };
        });
        const totalCost = costForParts(build.parts).toFixed(2);
        const sell = build.budget || '';
        const margin = sell ? (((sell - totalCost) / sell) * 100).toFixed(1) : '';
        const win = window.open('', '_blank', 'width=900,height=700');
        const html = `
            <html>
                <head><title>${build.name || 'Build'} BOM</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 16px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
                    th, td { border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }
                    th { background: #f5f5f5; text-align: left; }
                </style>
                </head>
                <body>
                    <h2>${build.name || 'Build'} Bill of Materials</h2>
                    <p>Date: ${new Date().toLocaleDateString()}</p>
                    <table>
                        <thead><tr><th>ID</th><th>Type</th><th>Brand</th><th>Model</th><th>Qty</th><th>Cost</th><th>Total</th></tr></thead>
                        <tbody>
                            ${rows
                                .map(
                                    (r) =>
                                        `<tr><td>${r.id}</td><td>${r.type}</td><td>${r.brand}</td><td>${r.model}</td><td>${r.qty}</td><td>$${r.cost}</td><td>$${r.total}</td></tr>`
                                )
                                .join('')}
                        </tbody>
                    </table>
                    <h4>Totals</h4>
                    <p>Cost: $${totalCost}${sell ? ` • Target sell: $${sell} • Margin: ${margin}%` : ''}</p>
                    <script>window.print();</script>
                </body>
            </html>
        `;
        win.document.write(html);
        win.document.close();
    };

    const preBuiltTotals = useMemo(() => {
        const partsTotal = (preBuiltForm.parts || []).reduce((s, p) => s + (Number(p.cost) || 0) * (p.qty || 1) + (Number(p.shipCost) || 0), 0);
        const taxRate = Number(preBuiltForm.taxPercent) || 0;
        const tax = partsTotal * (taxRate / 100);
        const total = partsTotal + tax;
        const sell = Number(preBuiltForm.targetSell || 0);
        const profit = sell - total;
        const margin = sell ? (profit / sell) * 100 : 0;
        const latestArrivalDays = Math.max(0, ...(preBuiltForm.parts || []).map((p) => Number(p.shippingDays) || 0));
        return { partsTotal, tax, total, sell, profit, margin, latestArrivalDays };
    }, [preBuiltForm]);

    const addPrePart = () => {
        if (!prePart.name.trim()) return;
        setPreBuiltForm((prev) => ({ ...prev, parts: [...prev.parts, { ...prePart, id: Date.now() }] }));
        setPrePart({ name: '', category: '', link: '', vendor: '', cost: '', shippingDays: '', qty: 1, condition: '', sku: '', notes: '', tax: '', shipCost: '' });
    };

    const removePrePart = (id) => {
        setPreBuiltForm((prev) => ({ ...prev, parts: prev.parts.filter((p) => p.id !== id) }));
    };

    const toast = (message, success = true, persist = false) => {
        setToastState({ message, success, visible: true });
        if (!persist) {
            setTimeout(() => setToastState((prev) => ({ ...prev, visible: false })), 2200);
        }
    };

    const exportInvoicePdf = (deal) => {
        const build = builds.find((b) => b.id === deal.buildId);
        const partsArr = build ? build.parts : [];
        const totalCost = costForParts(partsArr).toFixed(2);
        const sell = Number(deal.amount || deal.budget || 0).toFixed(2);
        const margin = sell && sell !== '0.00' ? (((sell - totalCost) / sell) * 100).toFixed(1) : '';
        const win = window.open('', '_blank', 'width=900,height=700');
        const rows = (partsArr || [])
            .map((p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id) || {};
                const qty = p.qty || 1;
                const cost = latestPrice(p.inventory_id);
                return `<tr><td>${p.inventory_id}</td><td>${item.typeNormalized || ''}</td><td>${item.brand || ''}</td><td>${item.model || ''}</td><td>${qty}</td><td>$${cost}</td></tr>`;
            })
            .join('');
        const html = `
            <html>
            <head><title>Invoice - ${deal.name}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 16px; }
                table { width: 100%; border-collapse: collapse; margin-top: 12px; }
                th, td { border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; text-align:left; }
                th { background: #f5f5f5; }
            </style>
            </head>
            <body>
                <h2>Invoice</h2>
                <p><strong>Deal:</strong> ${deal.name}</p>
                <p><strong>Client:</strong> ${deal.client || ''}</p>
                <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                <table>
                    <thead><tr><th>ID</th><th>Type</th><th>Brand</th><th>Model</th><th>Qty</th><th>Cost</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
                <h4>Totals</h4>
                <p>Cost: $${totalCost} • Sell: $${sell || '—'} ${margin ? `• Margin: ${margin}%` : ''}</p>
                <script>window.print();</script>
            </body>
            </html>
        `;
        win.document.write(html);
        win.document.close();
    };

    const addPartToBuild = () => {
        if (!partSelection.inventory_id || partSelection.qty <= 0) return;
        setBuildForm((prev) => {
            const exists = prev.parts.find((p) => p.inventory_id === partSelection.inventory_id);
            let parts;
            if (exists) {
                parts = prev.parts.map((p) =>
                    p.inventory_id === partSelection.inventory_id ? { ...p, qty: Number(partSelection.qty) } : p
                );
            } else {
                const inv = fullInventory.find((i) => i.inventory_id === partSelection.inventory_id);
                parts = [
                    ...prev.parts,
                    {
                        inventory_id: partSelection.inventory_id,
                        qty: Number(partSelection.qty),
                        label: inv ? `${inv.item_type} Â· ${inv.brand} ${inv.model}` : partSelection.inventory_id
                    }
                ];
            }
            return { ...prev, parts };
        });
        setPartSelection({ inventory_id: '', qty: 1 });
    };

    const removePartFromBuild = (inventory_id) => {
        setBuildForm((prev) => ({ ...prev, parts: prev.parts.filter((p) => p.inventory_id !== inventory_id) }));
    };

    const compatibilityIssues = useCallback((parts) => {
        const cpu = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'CPU');
        const mb = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'MOTHERBOARD');
        const psu = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'PSU' || (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'POWER SUPPLY');
        const gpus = parts.filter((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'GPU');
        const rams = parts.filter((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'RAM');
        const fans = parts.filter((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'FAN');
        const drives = parts.filter((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'STORAGE' || (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'SSD' || (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'HDD');
        const caseItem = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'CASE');
        const coolerItem = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'CPU COOLER');
        const osItem = parts.find((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'OS');
        const psuCables = parts.filter((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'PSU CABLE');

        const issues = [];
        if (cpu && mb) {
            const cpuItem = fullInventory.find((i) => i.inventory_id === cpu.inventory_id);
            const mbItem = fullInventory.find((i) => i.inventory_id === mb.inventory_id);
            if (cpuItem && mbItem && cpuItem.socketNormalized && mbItem.socketNormalized && cpuItem.socketNormalized !== mbItem.socketNormalized) {
                issues.push(`CPU socket ${cpuItem.socketNormalized} ≠ motherboard socket ${mbItem.socketNormalized}`);
            }
            // DDR match
            const mbDdr = mbItem?.ddrType;
            const ramMismatch = rams.some((p) => {
                const ramItem = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                return mbDdr && ramItem?.ddrType && ramItem.ddrType !== mbDdr;
            });
            if (mbDdr && ramMismatch) {
                issues.push(`RAM DDR type mismatch (board ${mbDdr})`);
            }
            // RAM speed ceiling
            const mbMaxSpeed = mbItem?.ram_speed_mhz || mbItem?.ramSpeed || 0;
            if (mbMaxSpeed) {
                const tooFast = rams.some((p) => {
                    const ramItem = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                    return ramItem?.ramSpeed && ramItem.ramSpeed > mbMaxSpeed + 50;
                });
                if (tooFast) {
                    issues.push(`RAM speed exceeds board spec (~${mbMaxSpeed} MHz); expect downclock or instability.`);
                }
            }
            // Channel utilization
            const boardChannels = mbItem?.channels || 0;
            const stickCount = rams.reduce((s, p) => s + (p.qty || 1), 0);
            if (boardChannels >= 2 && stickCount === 1) {
                issues.push('Single-stick on dual/quad-channel board; bandwidth will drop.');
            }
        }
        if (psu) {
            const psuItem = fullInventory.find((i) => i.inventory_id === psu.inventory_id);
            const psuWattsMatch = psuItem?.details?.match(/(\d+)\s*w(?!h)/i);
            const psuWatts = psuWattsMatch ? Number(psuWattsMatch[1]) : 0;
            const railMatch = psuItem?.details?.match(/12v[^\\d]*(\\d+(?:\\.\\d+)?)\\s*a/i);
            const railWatts = railMatch ? Number(railMatch[1]) * 12 : 0;

            const totalTdp = parts.reduce((sum, p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                return sum + (item?.tdp || 0);
            }, 0);
            const driveWatt = drives.reduce((sum, p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                const subtype = item?.storageSubtype || '';
                const per = subtype === 'HDD' ? 8 : subtype === 'SSD' || subtype === 'NVMe' ? 4 : 6;
                return sum + per * (p.qty || 1);
            }, 0);
            const fanWatt = fans.reduce((sum, p) => sum + 3 * (p.qty || 1), 0);
            const slotOverhead = gpus.length * 75; // PCIe slot power
            const misc = 25;
            const estimated = totalTdp + driveWatt + fanWatt + slotOverhead + misc;
            if (psuWatts && estimated > psuWatts * 0.8) issues.push(`Estimated draw ~${estimated}W vs PSU ${psuWatts}W (target <80%)`);
            if (railWatts && estimated > railWatts * 0.85) issues.push(`12V rail budget ~${railWatts}W may be tight for ${estimated}W load`);

            const totalPinsNeeded = gpus.reduce((s, p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                return s + (item?.pciePins || 0);
            }, 0);
            const cablesAvailable = psuItem?.pcieCables || psuItem?.pciePins || 0;
            if (totalPinsNeeded && cablesAvailable && totalPinsNeeded > cablesAvailable) {
                issues.push(`GPU PCIe pins needed ${totalPinsNeeded}, PSU cables ${cablesAvailable}`);
            }
        }
        if (!psu) {
            issues.push('No PSU selected; cannot validate power.');
        }
        if (!caseItem) {
            issues.push('No PC case selected.');
        }
        if (!drives.length) {
            issues.push('No storage (HDD/SSD/NVMe) selected.');
        }
        if (!coolerItem && cpu) {
            issues.push('No CPU cooler selected.');
        }
        if (fans.length === 0 && caseItem) {
            issues.push('No case fan selected.');
        }
        if (!osItem) {
            issues.push('No OS/license included.');
        }
        if (caseItem) {
            const caseInv = fullInventory.find((i) => i.inventory_id === caseItem.inventory_id);
            const caseMax = caseInv?.caseGpuMax || 0;
            const gpuLongest = gpus.reduce((m, p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                return Math.max(m, item?.lengthMm || 0);
            }, 0);
            if (caseMax && gpuLongest && gpuLongest > caseMax) {
                issues.push(`GPU length ${gpuLongest}mm exceeds case max ${caseMax}mm`);
            }
        }
        if (psu) {
            const psuItem = fullInventory.find((i) => i.inventory_id === psu.inventory_id);
            const totalPinsNeeded = gpus.reduce((s, p) => {
                const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                return s + (item?.pciePins || 0);
            }, 0);
            const cablesAvailable = (psuItem?.pcieCables || psuItem?.pciePins || 0) + psuCables.reduce((s, c) => s + (Number(c.qty) || 1), 0);
            if (totalPinsNeeded && totalPinsNeeded > cablesAvailable) {
                issues.push(`Need PSU PCIe cables (${totalPinsNeeded} pins required, ${cablesAvailable} available including loose cables)`);
            }
        }
        return issues;
    }, [fullInventory]);

    const reservePartsForBuild = (build) => {
        if (!build?.parts?.length) return;
        const newReservations = [];
        for (const p of build.parts) {
            const info = shortageForPart(p.inventory_id, p.qty || 1);
            if (info.missing > 0) {
                alert(`Cannot reserve: ${p.inventory_id} short by ${info.missing}`);
                return;
            }
            newReservations.push({ inventory_id: p.inventory_id, qty: p.qty || 1, buildId: build.id });
        }
        setReservations((prev) => [...prev.filter((r) => r.buildId !== build.id), ...newReservations]);
        alert('Parts reserved for this build.');
    };

    const resetBuildForm = () => {
        setBuildForm({
            id: null,
            name: '',
            client: '',
            budget: '',
            priority: 'Normal',
            due_date: '',
            status: 'Draft',
            notes: '',
            parts: []
        });
        setPartSelection({ inventory_id: '', qty: 1 });
    };

    const saveBuild = () => {
        if (!buildForm.name.trim()) {
            alert('Give this build a name.');
            return;
        }
        if (buildForm.parts.length === 0) {
            alert('Add at least one part to the build.');
            return;
        }
        if (buildForm.id) {
            setBuilds((prev) => prev.map((b) => (b.id === buildForm.id ? buildForm : b)));
        } else {
            setBuilds((prev) => [...prev, { ...buildForm, id: Date.now() }]);
        }
        resetBuildForm();
        setActivePage('builds');
    };

    const editBuild = (build) => {
        setBuildForm(build);
        setActivePage('builds');
    };

    const deleteBuild = (id) => {
        setBuilds((prev) => prev.filter((b) => b.id !== id));
        if (buildForm.id === id) {
            resetBuildForm();
        }
    };

    const buildShortageCount = (parts) =>
        parts.reduce((acc, p) => {
            const { missing } = shortageForPart(p.inventory_id, p.qty);
            return acc + (missing > 0 ? 1 : 0);
        }, 0) +
        (parts.some((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'STORAGE') ? 0 : 1) +
        (parts.some((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'CASE') ? 0 : 1) +
        (parts.some((p) => (fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '') === 'CPU COOLER') ? 0 : 1);

    const shortages = useMemo(() => {
        const map = {};
        builds.forEach((b) => {
            const requiredTypes = ['GPU', 'CASE', 'CPU COOLER', 'FAN', 'STORAGE', 'SSD', 'HDD', 'PSU', 'POWER SUPPLY', 'OS', 'PSU CABLE'];
            const haveType = {};
            (b.parts || []).forEach((p) => {
                const info = shortageForPart(p.inventory_id, p.qty);
                const tNorm = fullInventory.find((i) => i.inventory_id === p.inventory_id)?.typeNormalized || '';
                if (tNorm) haveType[tNorm] = true;
                if (info.missing > 0) {
                    if (!map[p.inventory_id]) {
                        map[p.inventory_id] = {
                            inventory_id: p.inventory_id,
                            needed: p.qty,
                            missing: info.missing,
                            available: info.available,
                            label: p.label || p.inventory_id,
                            builds: new Set(),
                            item_type: info.item?.item_type || ''
                        };
                    } else {
                        map[p.inventory_id].needed += p.qty;
                        map[p.inventory_id].missing += info.missing;
                        map[p.inventory_id].available = Math.min(map[p.inventory_id].available, info.available);
                    }
                    map[p.inventory_id].builds.add(b.name || 'Unnamed build');
                }
            });
            requiredTypes.forEach((rt) => {
                const present = Object.keys(haveType).some((t) => t === rt);
                if (present) return;
                const syntheticId = `${b.id || b.name || 'build'}-missing-${rt}`;
                if (!map[syntheticId]) {
                    map[syntheticId] = {
                        inventory_id: syntheticId,
                        needed: 1,
                        missing: 1,
                        available: 0,
                        label: `${rt} (required)`,
                        builds: new Set(),
                        item_type: rt
                    };
                }
                map[syntheticId].builds.add(b.name || 'Unnamed build');
            });
        });
        return Object.values(map).map((m) => ({ ...m, builds: Array.from(m.builds) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [builds, fullInventory]);

    const compatGaps = useMemo(() => {
        const gaps = [];
        const inventoryByType = (type) => fullInventory.filter((i) => i.typeNormalized === type && Number(i.qty) > 0);
        const cpus = inventoryByType('CPU');
        const mobos = inventoryByType('MOTHERBOARD');
        const rams = inventoryByType('RAM');

        cpus.forEach((cpu) => {
            const moboMatch = mobos.find((m) => m.socketNormalized && cpu.socketNormalized && m.socketNormalized === cpu.socketNormalized);
            if (!moboMatch) {
                gaps.push({
                    key: `cpu-${cpu.inventory_id}-mobo`,
                    need: 'MOTHERBOARD',
                    reason: `Need motherboard with socket ${cpu.socketNormalized || 'matching CPU'} for CPU ${cpu.model || cpu.inventory_id}`
                });
            } else {
                if (moboMatch.ddrType) {
                    const ramMatch = rams.find((r) => r.ddrType === moboMatch.ddrType);
                    if (!ramMatch) {
                        gaps.push({
                            key: `mobo-${moboMatch.inventory_id}-ram`,
                            need: 'RAM',
                            reason: `Need ${moboMatch.ddrType} RAM for motherboard ${moboMatch.model || moboMatch.inventory_id}`
                        });
                    }
                }
            }
        });

        // Global required types if CPUs exist but none on hand
        const requireIfCpu = ['GPU', 'CASE', 'CPU COOLER', 'FAN', 'STORAGE', 'PSU', 'POWER SUPPLY', 'OS', 'PSU CABLE'];
        if (cpus.length > 0) {
            requireIfCpu.forEach((t) => {
                const hasType = inventoryByType(t).length > 0;
                if (!hasType) {
                    gaps.push({
                        key: `global-missing-${t}`,
                        need: t,
                        reason: `No ${t} available; required to build systems with existing CPUs.`
                    });
                }
            });
        }

        return gaps;
    }, [fullInventory]);

    const displayShortages = useMemo(() => {
        const compatRows = compatGaps.map((g) => ({
            id: g.key,
            inventory_id: g.need || 'Compatibility gap',
            item_type: 'GAP',
            brand: '',
            model: '',
            qty: 0,
            status: 'MISSING',
            details: g.reason,
            missing: 1,
            available: 0,
            builds: ['N/A'],
            alternates: ''
        }));
        return [...shortages, ...compatRows];
    }, [shortages, compatGaps]);

    const shortagesStats = useMemo(() => {
        const blockers = shortages.length + compatGaps.length;
        const unitsMissing = shortages.reduce((s, i) => s + i.missing, 0) + compatGaps.length;
        const buildsAffected = new Set(shortages.flatMap((s) => s.builds)).size;
        const needReorder = shortages.filter((s) => s.available === 0).length + compatGaps.length;
        return { blockers, unitsMissing, buildsAffected, needReorder };
    }, [shortages, compatGaps]);

    const orderSuggestions = useMemo(() => {
        const baseTypes = [
            'CPU',
            'GPU',
            'MOTHERBOARD',
            'RAM',
            'PSU',
            'PSU CABLE',
            'CASE',
            'CPU COOLER',
            'FAN',
            'STORAGE',
            'SSD',
            'HDD',
            'GPU COOLER',
            'NETWORKING',
            'ROUTER',
            'SWITCH',
            'NIC',
            'OS'
        ];
        const typeTotals = {};
        fullInventory.forEach((item) => {
            const reservedQty = reservations.filter((r) => r.inventory_id === item.inventory_id).reduce((s, r) => s + (r.qty || 0), 0);
            const qty = Math.max(0, (Number(item.qty) || 0) - reservedQty);
            const key = item.typeNormalized || 'OTHER';
            typeTotals[key] = (typeTotals[key] || 0) + qty;
        });
        const lowTypes = baseTypes
            .map((t) => {
                const qty = typeTotals[t] || 0;
                const need = thresholdFor(t) - qty;
                return need > 0 ? { inventory_id: `TYPE-${t}`, label: t, item_type: t, missing: need, available: qty, builds: [] } : null;
            })
            .filter(Boolean);
        return [...shortages, ...lowTypes];
    }, [shortages, fullInventory, reservations, thresholdFor]);

    // Profit engine calculations
    const profitEngine = useMemo(() => {
        const conditionMultiplier = (item) => {
            const status = (item.test_status || item.status || '').toUpperCase();
            if (status.includes('UNT') || status.includes('UNTEST')) return 0.75;
            if (status.includes('IN USE')) return 0.92;
            return 1.0;
        };
        const trueCost = (item) => {
            const price = Number(item.price_paid) || 0;
            const inbound = Number(item.inbound_cost) || 0;
            const outbound = Number(item.outbound_cost) || 0;
            const platform = Number(item.platform_fees) || 0;
            const labor = Number(item.labor_estimate) || 0;
            return price + inbound + outbound + platform + labor;
        };
        const marketEstimate = (item) => {
            const base = Number(item.price_paid) || 0;
            const multiplier = conditionMultiplier(item);
            const median = base * 1.35 * multiplier;
            return {
                low: median * 0.9,
                mid: median,
                high: median * 1.15,
                expected: median
            };
        };
        const items = fullInventory.map((item) => {
            const cost = trueCost(item);
            const market = marketEstimate(item);
            const profit = market.expected - cost;
            const age = item.ageDays || 0;
            const daysHeld = Math.max(age, 1);
            const roi = cost ? (profit / cost) * 100 : 0;
            const profitPerDay = profit / daysHeld;
            const demand =
                daysHeld < 14 ? 'HOT' : daysHeld <= 45 ? 'NORMAL' : 'SLOW';
            return { item, cost, market, profit, roi, profitPerDay, demand, daysHeld };
        });
        const topItems = items
            .filter((i) => i.profitPerDay > 0)
            .sort((a, b) => b.profitPerDay - a.profitPerDay)
            .slice(0, 5);

        // build-level
        const buildProfiles = builds.map((b) => {
            const cost = costForParts(b.parts || []);
            const expected = Number(b.budget || 0) || (cost ? cost * 1.4 : 0);
            const profit = expected - cost;
            const issues = compatibilityIssues(b.parts || []);
            return { build: b, cost, expected, profit, roi: cost ? (profit / cost) * 100 : 0, issues };
        });
        const bestBuild = buildProfiles
            .filter((p) => p.profit > 0)
            .sort((a, b) => b.roi - a.roi)[0];

        const capitalVelocity = (() => {
            const totalProfit = items.reduce((s, i) => s + Math.max(0, i.profit), 0);
            const avgDays = items.length ? items.reduce((s, i) => s + i.daysHeld, 0) / items.length : 0;
            return avgDays ? totalProfit / avgDays : 0;
        })();

        return { items, topItems, bestBuild, capitalVelocity };
    }, [fullInventory, builds, costForParts, compatibilityIssues]);

    // notifications digest (placed after shortages are defined)
    useEffect(() => {
        const digest = [];
        if (stats.lowStock > 0) digest.push(`${stats.lowStock} item types are below thresholds.`);
        if (shortages.length > 0) digest.push(`${shortages.length} shortages blocking builds.`);
        const overdueOrders = orders.filter((o) => o.due_date && new Date(o.due_date) < new Date() && o.status !== 'Delivered');
        if (overdueOrders.length > 0) digest.push(`${overdueOrders.length} orders past due date.`);
        const lowMarginBuilds = builds.filter((b) => {
            const c = costForParts(b.parts || []);
            const sell = Number(b.budget || 0);
            if (!sell) return false;
            const m = (sell - c) / sell;
            return m < 0.18;
        });
        if (lowMarginBuilds.length > 0) digest.push(`${lowMarginBuilds.length} builds below 18% margin.`);
        const compIssueBuilds = builds.filter((b) => compatibilityIssues(b.parts || []).length > 0);
        if (compIssueBuilds.length > 0) digest.push(`${compIssueBuilds.length} builds with compatibility warnings.`);
        setNotifications(digest);
    }, [stats.lowStock, shortages, orders, builds, costForParts, compatibilityIssues]);

    const finTotals = useMemo(() => {
        const partsTotal = financialForm.parts.reduce((s, p) => s + (Number(p.cost) || 0), 0);
        const profit = (Number(financialForm.sellPrice) || 0) - partsTotal;
        const margin = partsTotal ? profit / partsTotal : 0;
        return { partsTotal, profit, margin };
    }, [financialForm]);

    const saveBizPlan = () => {
        if (!bizForm.month.trim()) {
            alert('Enter a month/period.');
            return;
        }
        const payload = { ...bizForm, id: bizForm.id || Date.now() };
        setBizPlans((prev) => {
            const existing = prev.find((b) => b.id === payload.id);
            if (existing) return prev.map((b) => (b.id === payload.id ? payload : b));
            return [...prev, payload];
        });
        setBizForm({ id: null, month: '', revenue: '', expenses: '', notes: '' });
    };

    const deleteBizPlan = (id) => {
        setBizPlans((prev) => prev.filter((b) => b.id !== id));
        if (bizForm.id === id) setBizForm({ id: null, month: '', revenue: '', expenses: '', notes: '' });
    };

    const saveSocial = () => {
        if (!socialForm.label.trim() || !socialForm.url.trim()) {
            alert('Add a label and URL');
            return;
        }
        const payload = { ...socialForm, id: socialForm.id || Date.now() };
        setSocialLinks((prev) => {
            const existing = prev.find((s) => s.id === payload.id);
            if (existing) return prev.map((s) => (s.id === payload.id ? payload : s));
            return [...prev, payload];
        });
        setSocialForm({ id: null, label: '', url: '', note: '' });
    };

    const deleteSocial = (id) => {
        setSocialLinks((prev) => prev.filter((s) => s.id !== id));
        if (socialForm.id === id) setSocialForm({ id: null, label: '', url: '', note: '' });
    };

    const alternatesFor = (item_type, excludeId) =>
        fullInventory
            .filter((i) => i.item_type === item_type && i.inventory_id !== excludeId && Number(i.qty) > 0)
            .sort((a, b) => Number(b.qty) - Number(a.qty))
            .slice(0, 3);

    const addTask = ({ title, category = 'General', status = 'Open', priority = 'Normal', notes = '' }) => {
        setTasks((prev) => [
            ...prev,
            {
                id: Date.now(),
                title,
                category,
                status,
                priority,
                notes,
                created_at: new Date().toISOString().split('T')[0]
            }
        ]);
    };

    const addRestockTask = (s) => {
        addTask({
            title: `Restock ${s.inventory_id}`,
            category: 'Restock',
            status: 'Open',
            priority: 'High',
            notes: `Missing ${s.missing} for ${s.builds.join(', ')}`
        });
        alert('Restock task added to Tasks.');
    };

    const markOrdered = (s) => {
        addTask({
            title: `Ordered ${s.inventory_id}`,
            category: 'Order',
            status: 'In Progress',
            priority: 'Normal',
            notes: `Placed order to cover shortage of ${s.missing}.`
        });
        alert('Marked as ordered and logged in Tasks.');
    };

    const prefillOrderFromShortage = (s) => {
        const preferred = suppliers.find((sup) =>
            (sup.preferred_items || '').toLowerCase().includes((s.item_type || '').toLowerCase())
        ) || suppliers[0] || {};
        const itemsLine = `${s.label || s.inventory_id || 'Part'} x${s.missing ?? 1} (${s.need || s.item_type || ''})`;
        const noteLine = `Shortage auto-fill • Builds: ${(s.builds || []).join(', ') || 'N/A'} • Missing ${s.missing ?? 1}`;
        setOrderForm((prev) => ({
            ...prev,
            id: null,
            vendor: preferred.name || '',
            channel: preferred.channel || '',
            status: 'Draft',
            items: itemsLine,
            notes: noteLine
        }));
        setActivePage('orders');
    };

    const addSupplier = (e) => {
        e.preventDefault();
        if (!supplierForm.name.trim()) return;
        setSuppliers((prev) => [...prev, { ...supplierForm, id: Date.now() }]);
        setSupplierForm({ name: '', contact: '', channel: '', website: '', notes: '', preferred_items: '' });
    };

    const saveOrder = () => {
        if (!orderForm.vendor.trim()) {
            alert('Add a vendor name.');
            return;
        }
        if (orderForm.id) {
            setOrders((prev) => prev.map((o) => (o.id === orderForm.id ? orderForm : o)));
        } else {
            setOrders((prev) => [...prev, { ...orderForm, id: Date.now(), created_at: new Date().toISOString().split('T')[0] }]);
        }
        setOrderForm({
            id: null,
            vendor: '',
            channel: '',
            status: 'Draft',
            total: '',
            due_date: '',
            tracking: '',
            items: '',
            notes: ''
        });
    };

    const editOrder = (o) => setOrderForm(o);
    const deleteOrder = (id) => setOrders((prev) => prev.filter((o) => o.id !== id));

    const saveTask = () => {
        if (!taskForm.title.trim()) {
            alert('Add a task title.');
            return;
        }
        if (taskForm.id) {
            setTasks((prev) => prev.map((t) => (t.id === taskForm.id ? taskForm : t)));
        } else {
            setTasks((prev) => [
                ...prev,
                { ...taskForm, id: Date.now(), created_at: new Date().toISOString().split('T')[0] }
            ]);
        }
        setTaskForm({ id: null, title: '', category: 'General', status: 'Open', priority: 'Normal', due_date: '', notes: '' });
    };

    const editTask = (t) => setTaskForm(t);
    const deleteTask = (id) => setTasks((prev) => prev.filter((t) => t.id !== id));

    const addFinPart = () => {
        if (!finPart.name.trim() || !finPart.cost) return;
        setFinancialForm((prev) => ({ ...prev, parts: [...prev.parts, { ...finPart, cost: Number(finPart.cost) }] }));
        setFinPart({ name: '', type: '', link: '', cost: '' });
    };

    const removeFinPart = (idx) => {
        setFinancialForm((prev) => ({ ...prev, parts: prev.parts.filter((_, i) => i !== idx) }));
    };

    const saveFinancial = () => {
        if (!financialForm.name.trim()) {
            alert('Add a build name.');
            return;
        }
        const payload = { ...financialForm, id: financialForm.id || Date.now() };
        setFinancialBuilds((prev) => {
            const existing = prev.find((b) => b.id === payload.id);
            if (existing) return prev.map((b) => (b.id === payload.id ? payload : b));
            return [...prev, payload];
        });
        setFinancialForm({ id: null, name: '', parts: [], sellPrice: '' });
    };

    const deleteFinancial = (id) => {
        setFinancialBuilds((prev) => prev.filter((b) => b.id !== id));
        if (financialForm.id === id) setFinancialForm({ id: null, name: '', parts: [], sellPrice: '' });
    };

    const nextCopyName = (name) => {
        const match = name.match(/_(\d+)$/);
        if (match) {
            const n = parseInt(match[1], 10) + 1;
            return name.replace(/_\d+$/, `_${n}`);
        }
        return `${name || 'Plan'}_1`;
    };

    const duplicateFinancialForm = () => {
        if (!financialForm.name.trim()) {
            alert('Add a build name before duplicating.');
            return;
        }
        const copy = { ...financialForm, id: Date.now(), name: nextCopyName(financialForm.name.trim()) };
        setFinancialBuilds((prev) => [...prev, copy]);
        setFinancialForm(copy);
        toast('Copied plan', true);
    };

    return (
        <div className="min-h-screen bg-slate-50 flex">
            {/* Sidebar */}
            <div className={`${sidebarOpen ? 'w-64' : 'w-16'} transition-all duration-200 bg-white border-r border-gray-200 shadow-sm flex flex-col`}>
                <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-3 flex items-center gap-2 text-slate-700 hover:text-sky-600">
                    <span className="text-lg">☰</span>
            {sidebarOpen && <span className="font-semibold text-sm">Menu</span>}
        </button>
        <nav className="flex-1 overflow-y-auto">
            {['Inventory', 'Planning', 'Supply', 'Business', 'Actions', 'Info'].map((section) => (
                <div key={section} className="mb-2">
                            {sidebarOpen && <div className="px-3 py-1 text-[11px] uppercase text-slate-500 font-semibold">{section}</div>}
                            {navItems.filter((n) => n.section === section).map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => setActivePage(item.id)}
                                    className={`w-full px-3 py-2 text-sm flex items-center gap-2 text-left transition ${
                                        activePage === item.id ? 'bg-sky-50 text-sky-700 border-l-4 border-sky-500 font-semibold' : 'text-slate-700 hover:bg-slate-50'
                                    }`}
                                >
                                    <span className="text-lg">{item.icon}</span>
                                    {sidebarOpen && <span>{item.label}</span>}
                                </button>
                            ))}
                        </div>
                    ))}
            </nav>
        </div>

        {helpOpen && (
            <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-30 pt-10 md:pt-16">
                <div className="bg-white rounded-2xl shadow-2xl p-5 max-w-lg w-[90%]">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-slate-900">{navItems.find((n) => n.id === activePage)?.label || 'Help'}</h3>
                        <button onClick={() => setHelpOpen(false)} className="text-slate-500 hover:text-slate-700 text-lg">×</button>
                    </div>
                    <p className="text-sm text-slate-700 whitespace-pre-line">{helpCopy[activePage] || 'No help text yet.'}</p>
                </div>
            </div>
        )}
        {toastState.visible && (
            <div
                className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg text-sm font-semibold ${
                    toastState.success ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'
                }`}
            >
                {toastState.message}
            </div>
        )}
        {/* Main */}
        <div className="flex-1 p-4 md:p-6">
            <div className="bg-gradient-to-r from-sky-500 to-indigo-500 text-white rounded-2xl p-6 shadow-lg mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between relative">
                <div className="pr-16">
                    <p className="text-sm opacity-90">Dashboard</p>
                    <h1 className="text-3xl font-extrabold leading-tight">
                        {activePage === 'inventory' ? 'Inventory Management' : navItems.find((n) => n.id === activePage)?.label}
                    </h1>
                    <p className="text-sm opacity-90 mt-1">
                        {activePage === 'inventory'
                            ? 'Search, filter, and keep your stock under control.'
                            : navItems.find((n) => n.id === activePage)?.blurb}
                    </p>
                </div>
                <button
                    onClick={() => setHelpOpen(true)}
                    className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/20 text-white border border-white/30 hover:bg-white/30 transition absolute right-4 top-4"
                    title="Help"
                >
                    ?
                </button>
                {activePage === 'inventory' && (
                    <div className="flex flex-wrap gap-3 md:ml-auto md:mr-12">
                        <button
                            onClick={() => { setShowForm(true); setEditingItem(null); resetForm(); }}
                            className="bg-white text-sky-600 font-semibold px-4 py-2 rounded-lg shadow hover:-translate-y-0.5 transform transition"
                        >
                            + Add New Item
                        </button>
                        <button
                            onClick={exportToCSV}
                            className="bg-emerald-500 text-white font-semibold px-4 py-2 rounded-lg shadow hover:bg-emerald-600 transition"
                        >
                            Export CSV
                        </button>
                        <button
                            onClick={() => setThresholdModal(true)}
                            className="bg-white/80 text-slate-800 font-semibold px-4 py-2 rounded-lg shadow hover:-translate-y-0.5 transform transition"
                        >
                            Low-stock rules
                        </button>
                        <button
                            onClick={async () => {
                                try {
                                    setLoading(true);
                                    toast('Running normalization…', true, true);
                                    await syncNormalizedTypes(fullInventory);
                                    await fetchInventory();
                                    await fetchStats();
                                    toast('Successfully normalized data', true);
                                } catch (err) {
                                    toast('Normalization failed', false);
                                } finally {
                                    setLoading(false);
                                }
                            }}
                            className="bg-white/80 text-slate-800 font-semibold px-4 py-2 rounded-lg shadow hover:-translate-y-0.5 transform transition"
                        >
                            Re-run normalization
                        </button>
                        <button
                            onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
                            className="bg-white/80 text-slate-800 font-semibold px-4 py-2 rounded-lg shadow hover:-translate-y-0.5 transform transition"
                        >
                            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
                        </button>
                    </div>
                )}
            </div>

                {activePage === 'inventory' && (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                            <StatCard title="Total Items" value={stats.total} accent="bg-sky-500" />
                            <StatCard title="Available" value={stats.available} accent="bg-emerald-500" />
                            <StatCard title="In Use" value={stats.inUse} accent="bg-amber-500" />
                            <StatCard title="Low Stock" value={stats.lowStock} accent="bg-rose-500" />
                        </div>

                        {notifications.length > 0 && (
                            <div className="mb-4 border border-amber-200 bg-amber-50 rounded-2xl p-3 text-sm text-amber-800">
                                <div className="font-semibold text-amber-900 mb-1">Digest</div>
                                <ul className="list-disc list-inside space-y-1">
                                    {notifications.map((n, idx) => (
                                        <li key={idx}>{n}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div className="mb-6">
                            <h4 className="text-sm text-slate-500 mb-2">Type overview</h4>
                            <div className="space-y-3">
                                {['Components', 'Networking', 'Peripherals', 'Tools', 'Other'].map((group) => (
                                    <div key={group} className="border border-slate-100 bg-white rounded-xl p-3 shadow-sm">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="text-sm font-semibold text-slate-900">{group}</div>
                                            <div className="text-xs text-slate-500">
                                                {groupedOverview[group] ? Object.values(groupedOverview[group]).reduce((s, v) => s + v.count, 0) : 0} items
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                            {groupedOverview[group] &&
                                                Object.entries(groupedOverview[group])
                                                    .sort((a, b) => b[1].count - a[1].count)
                                                    .map(([key, info]) => (
                                                        <div
                                                            key={key}
                                                            className="border border-slate-100 rounded-lg px-3 py-2 flex items-center justify-between cursor-pointer hover:border-sky-200"
                                                            onClick={() => setExpandedType((prev) => (prev === key ? null : key))}
                                                        >
                                                            <div>
                                                                <div className="text-xs font-semibold text-slate-900">{key}</div>
                                                                <div className="text-[11px] text-slate-500">{info.count} items</div>
                                                            </div>
                                                            <span className={`px-2 py-1 rounded-full text-[11px] ${info.low > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                                                {info.low > 0 ? `${info.low} low` : 'OK'}
                                                            </span>
                                                        </div>
                                                    ))}
                                            {!groupedOverview[group] && <div className="text-xs text-slate-500">No items</div>}
                                        </div>

                                        {expandedType && groupedOverview[group]?.[expandedType] && (
                                            <div className="mt-2 border-t border-slate-100 pt-2">
                                                <div className="text-[11px] font-semibold text-slate-600 mb-1">Models in {expandedType}</div>
                                                <div className="max-h-56 overflow-y-auto space-y-2">
                                                    {Object.entries(
                                                        fullInventory
                                                            .filter((i) => i.typeNormalized === expandedType)
                                                            .reduce((acc, i) => {
                                                                const key =
                                                                    expandedType === 'CPU'
                                                                        ? i.socketNormalized || 'Unknown socket'
                                                                        : expandedType === 'STORAGE'
                                                                        ? i.storageSubtype || 'Other storage'
                                                                        : i.socketNormalized || 'General';
                                                                acc[key] = acc[key] || [];
                                                                acc[key].push(i);
                                                                return acc;
                                                            }, {})
                                                    ).map(([subKey, items]) => (
                                                        <div key={subKey}>
                                                            <div className="text-[11px] font-semibold text-slate-700 mb-1">{subKey}</div>
                                                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                                                                {items.map((i) => (
                                                                    <button
                                                                        key={i.id}
                                                                        className="text-left text-[11px] px-2 py-1 rounded hover:bg-sky-50 border border-slate-100"
                                                                        onClick={() => setDetailItem(i)}
                                                                    >
                                                                        {i.brand ? `${i.brand} ` : ''}
                                                                        {i.model || i.inventory_id}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="mb-6 grid grid-cols-1 xl:grid-cols-4 gap-4 items-center">
                            <form onSubmit={handleImport} className="flex flex-wrap gap-2 items-center xl:col-span-2">
                                <label className="px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-sm cursor-pointer hover:border-sky-300 transition">
                                    <input type="file" accept=".csv" onChange={(e) => setImportFile(e.target.files[0])} className="hidden" />
                                    <span className="text-sm font-medium text-gray-700">Choose CSV</span>
                                </label>
                                <span className="text-sm text-gray-500 truncate max-w-[120px]">{importFile ? importFile.name : 'No file chosen'}</span>
                                <button type="submit" className="bg-purple-500 text-white font-semibold px-3 py-2 rounded-lg shadow hover:bg-purple-600 transition">
                                    Import CSV
                                </button>
                            </form>
                            <div className="flex gap-2 text-xs flex-wrap">
                                <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700">Sorted by: {sortField} ({sortOrder})</span>
                                {lowOnly && <span className="px-2 py-1 rounded-full bg-rose-100 text-rose-700">Low stock filter</span>}
                            </div>
                        </div>

                        <div className="mb-6 grid grid-cols-1 xl:grid-cols-4 gap-4 items-center">
                            <div className="xl:col-span-2">
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="Search by brand, model, type, or details..."
                                        value={search}
                                        onChange={(e) => { setPage(1); setSearch(e.target.value); }}
                                        className="w-full pl-3 pr-3 py-2.5 border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                                    />
                                </div>
                            </div>
                            <div>
                                <select
                                    value={statusFilter}
                                    onChange={(e) => { setPage(1); setStatusFilter(e.target.value); }}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                                >
                                    <option value="">All Statuses</option>
                                    <option value="AVAILABLE">Available</option>
                                    <option value="IN USE">In Use</option>
                                    <option value="UNTESTED">Untested</option>
                                </select>
                            </div>
                            <div>
                                <select
                                    value={itemTypeFilter}
                                    onChange={(e) => { setPage(1); setItemTypeFilter(e.target.value); }}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                                >
                                    <option value="">All types</option>
                                    {Array.from(
                                        new Set([
                                            ...inventory.map((i) => i.typeNormalized),
                                            'CPU',
                                            'GPU',
                                            'MOTHERBOARD',
                                            'RAM',
                                            'PSU',
                                            'CASE',
                                            'CPU COOLER',
                                            'FAN',
                                            'STORAGE',
                                            'SSD',
                                            'HDD',
                                            'NETWORKING',
                                            'ROUTER',
                                            'SWITCH',
                                            'NIC',
                                            'KEYBOARD',
                                            'MICE',
                                            'MONITOR',
                                            'HEADSET'
                                        ])
                                    )
                                        .filter(Boolean)
                                        .sort()
                                        .map((t) => (
                                            <option key={t} value={t}>
                                                {t}
                                            </option>
                                        ))}
                                </select>
                            </div>
                        </div>

                        <div className="mb-4 grid grid-cols-1 xl:grid-cols-4 gap-4 items-center">
                            <div>
                                <select
                                    value={brandFilter}
                                    onChange={(e) => { setPage(1); setBrandFilter(e.target.value); }}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                                >
                                    <option value="">All brands</option>
                                    {Array.from(new Set(inventory.map((i) => i.brand))).filter(Boolean).sort().map((b) => (
                                        <option key={b} value={b}>{b}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={lowOnly}
                                    onChange={(e) => { setPage(1); setLowOnly(e.target.checked); }}
                                    className="h-4 w-4"
                                />
                                <span className="text-sm text-slate-700">Low stock only</span>
                            </div>
                        </div>
                    </>
                )}

                {activePage === 'inventory' && selectedItems.length > 0 && (
                    <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 shadow-sm">
                        <span className="font-semibold">{selectedItems.length} selected</span>
                        <select
                            value={bulkAction}
                            onChange={(e) => setBulkAction(e.target.value)}
                            className="border border-amber-200 rounded-lg px-3 py-1.5 bg-white"
                        >
                            <option value="">Bulk action</option>
                            <option value="update">Set status to In Use</option>
                            <option value="delete">Delete</option>
                        </select>
                        <button onClick={handleBulkAction} className="px-3 py-1.5 rounded-lg bg-amber-500 text-white font-semibold hover:bg-amber-600 transition">
                            Apply
                        </button>
                        <button onClick={() => setSelectedItems([])} className="text-sm underline">
                            Clear
                        </button>
                    </div>
                )}

                {activePage === 'inventory' && showForm && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50">
                        <div
                            style={{ position: 'absolute', top: modalAnchor.top, left: modalAnchor.left, transform: 'translate(-50%, -50%)' }}
                            className={`p-6 rounded shadow-2xl w-full max-w-lg max-h-screen overflow-y-auto ${
                                theme === 'dark' ? 'bg-slate-900 text-slate-100 border border-slate-700' : 'bg-white text-slate-900'
                            }`}
                        >
                            <h2 className="text-xl font-bold mb-4">{editingItem ? 'Edit Item' : 'Add New Item'}</h2>
                            <form onSubmit={handleFormSubmit} className="space-y-4">
                                <input name="inventory_id" value={formData.inventory_id} onChange={handleInputChange} placeholder="Inventory ID" required className="w-full border p-2 rounded" />
                                <input name="item_type" value={formData.item_type} onChange={handleInputChange} placeholder="Item Type" className="w-full border p-2 rounded" />
                                <input name="brand" value={formData.brand} onChange={handleInputChange} placeholder="Brand" className="w-full border p-2 rounded" />
                                <input name="model" value={formData.model} onChange={handleInputChange} placeholder="Model" className="w-full border p-2 rounded" />
                                <input name="component" value={formData.component} onChange={handleInputChange} placeholder="Component" className="w-full border p-2 rounded" />
                                <input name="qty" type="number" value={formData.qty} onChange={handleInputChange} placeholder="Quantity" className="w-full border p-2 rounded" />
                                <textarea name="details" value={formData.details} onChange={handleInputChange} placeholder="Details" className="w-full border p-2 rounded" />
                                <input name="socket_or_interface" value={formData.socket_or_interface} onChange={handleInputChange} placeholder="Socket/Interface" className="w-full border p-2 rounded" />
                                <select name="status" value={formData.status} onChange={handleInputChange} className="w-full border p-2 rounded">
                                    <option value="AVAILABLE">Available</option>
                                    <option value="IN USE">In Use</option>
                                    <option value="UNTESTED">Untested</option>
                                </select>
                                <input name="used_in" value={formData.used_in} onChange={handleInputChange} placeholder="Used In" className="w-full border p-2 rounded" />
                                <input name="ownership" value={formData.ownership} onChange={handleInputChange} placeholder="Ownership" className="w-full border p-2 rounded" />
                                <input name="test_status" value={formData.test_status} onChange={handleInputChange} placeholder="Test Status" className="w-full border p-2 rounded" />
                                <input name="cooler_required" value={formData.cooler_required} onChange={handleInputChange} placeholder="Cooler Required" className="w-full border p-2 rounded" />
                                <textarea name="notes" value={formData.notes} onChange={handleInputChange} placeholder="Notes" className="w-full border p-2 rounded" />
                                <input name="photo_refs" value={formData.photo_refs} onChange={handleInputChange} placeholder="Photo Refs" className="w-full border p-2 rounded" />
                                <input name="price_paid" type="number" step="0.01" value={formData.price_paid} onChange={handleInputChange} placeholder="Price Paid" className="w-full border p-2 rounded" />
                                <input name="source" value={formData.source} onChange={handleInputChange} placeholder="Source" className="w-full border p-2 rounded" />
                                <input name="seller" value={formData.seller} onChange={handleInputChange} placeholder="Seller" className="w-full border p-2 rounded" />
                                <input name="location_bin" value={formData.location_bin} onChange={handleInputChange} placeholder="Location Bin" className="w-full border p-2 rounded" />
                                <input name="location_shelf" value={formData.location_shelf} onChange={handleInputChange} placeholder="Location Shelf" className="w-full border p-2 rounded" />
                                <textarea name="location_notes" value={formData.location_notes} onChange={handleInputChange} placeholder="Location Notes" className="w-full border p-2 rounded" />
                                <div className="flex justify-end space-x-2">
                                    <button
                                        type="button"
                                        onClick={() => { setShowForm(false); setEditingItem(null); }}
                                        className={`${theme === 'dark' ? 'bg-slate-700' : 'bg-gray-500'} text-white px-4 py-2 rounded`}
                                    >
                                        Cancel
                                    </button>
                                    <button type="submit" className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                                        Save
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {activePage === 'inventory' ? (
                    loading ? (
                        <div className="flex items-center gap-3 text-gray-600">
                            <div className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
                            Loading inventory...
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto shadow-sm border border-gray-200 rounded-2xl bg-white">
                                <table className="min-w-full text-sm">
                                    <thead className="bg-gray-50 text-gray-600 uppercase tracking-wide text-xs">
                                        <tr>
                                            <th className="py-3 px-4 text-left border-b">
                                                <input
                                                    type="checkbox"
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSelectedItems(pageItems.map((item) => item.id));
                                                        } else {
                                                            setSelectedItems([]);
                                                        }
                                                    }}
                                                    checked={selectedItems.length === pageItems.length && pageItems.length > 0}
                                                />
                                            </th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('inventory_id')}>
                                                Inventory ID {sortField === 'inventory_id' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('item_type')}>
                                                Item Type {sortField === 'item_type' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('brand')}>
                                                Brand {sortField === 'brand' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('model')}>
                                                Model {sortField === 'model' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b">Socket</th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('qty')}>
                                                Qty {sortField === 'qty' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b cursor-pointer" onClick={() => handleSort('status')}>
                                                Status {sortField === 'status' && (sortOrder === 'asc' ? '^' : 'v')}
                                            </th>
                                            <th className="py-3 px-4 text-left border-b">Details</th>
                                            <th className="py-3 px-4 text-left border-b">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {pageItems.map((item) => (
                                            <tr key={item.id} className={`${item.qty < thresholdFor(item.typeNormalized) ? 'bg-rose-50' : 'bg-white'} hover:bg-sky-50 transition`}>
                                                <td className="py-3 px-4">
                                                    <input type="checkbox" checked={selectedItems.includes(item.id)} onChange={() => handleSelectItem(item.id)} />
                                                </td>
                                                <td className="py-3 px-4 font-semibold text-gray-800">{item.inventory_id}</td>
                                                <td className="py-3 px-4 text-gray-700">{item.typeNormalized}</td>
                                                <td className="py-3 px-4 text-gray-700">{item.brand}</td>
                                                <td className="py-3 px-4 text-gray-700">{item.model}</td>
                                                <td className="py-3 px-4 text-gray-700 text-xs">{item.socketNormalized || 'â€”'}</td>
                                                <td className="py-3 px-4 text-gray-700">{item.qty}</td>
                                                <td className="py-3 px-4">
                                                    <span className={statusBadge(item.status)}>{item.status}</span>
                                                </td>
                                                <td className="py-3 px-4 text-gray-600 max-w-xs">{item.details}</td>
                                                <td className="py-3 px-4 space-x-2">
                                                    <button onClick={() => handleEdit(item)} className="px-3 py-1 rounded-lg border border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100 shadow-sm">
                                                        Edit
                                                    </button>
                                                    <button onClick={() => handleDelete(item.id)} className="px-3 py-1 rounded-lg border border-rose-200 text-rose-700 bg-rose-50 hover:bg-rose-100 shadow-sm">
                                                        Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                        {filteredInventory.length === 0 && (
                                            <tr>
                                                <td colSpan="9" className="py-6 text-center text-gray-500">
                                                    No items found. Try adjusting your filters.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            <div className="mt-4 flex justify-center items-center gap-3 text-sm">
                                <button
                                    onClick={() => setPage(page - 1)}
                                    disabled={page === 1}
                                    className="px-4 py-2 rounded-lg border border-gray-200 bg-white shadow-sm disabled:opacity-50"
                                >
                                    Previous
                                </button>
                                <span className="px-2 py-1 rounded bg-gray-100 text-gray-700">Page {page} of {totalPages}</span>
                                <button
                                    onClick={() => setPage(page + 1)}
                                    disabled={page === totalPages}
                                    className="px-4 py-2 rounded-lg border border-gray-200 bg-white shadow-sm disabled:opacity-50"
                                >
                                    Next
                                </button>
                            </div>
                        </>
                    )
                ) : activePage === 'builds' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <div className="xl:col-span-2 space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Build brief</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{buildForm.id ? 'Edit plan' : 'New plan'}</h3>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={resetBuildForm} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">
                                            Clear
                                        </button>
                                        <button onClick={saveBuild} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">
                                            Save plan
                                        </button>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 gap-3">
                                    <input name="name" value={buildForm.name} onChange={handleBuildChange} placeholder="Build name (e.g., 4K Creator, Budget LAN)" className="border rounded-lg px-3 py-2" />
                                    <input name="client" value={buildForm.client} onChange={handleBuildChange} placeholder="Client / Project" className="border rounded-lg px-3 py-2" />
                                    <input name="budget" type="number" value={buildForm.budget} onChange={handleBuildChange} placeholder="Target budget $" className="border rounded-lg px-3 py-2" />
                                    <select name="priority" value={buildForm.priority} onChange={handleBuildChange} className="border rounded-lg px-3 py-2">
                                        <option>Low</option>
                                        <option>Normal</option>
                                        <option>High</option>
                                        <option>Urgent</option>
                                    </select>
                                    <input name="due_date" type="date" value={buildForm.due_date} onChange={handleBuildChange} className="border rounded-lg px-3 py-2" />
                                    <select name="status" value={buildForm.status} onChange={handleBuildChange} className="border rounded-lg px-3 py-2">
                                        <option>Draft</option>
                                        <option>Waiting parts</option>
                                        <option>Building</option>
                                        <option>Testing</option>
                                        <option>Ready</option>
                                    </select>
                                </div>
                                <textarea
                                    name="notes"
                                    value={buildForm.notes}
                                    onChange={handleBuildChange}
                                    placeholder="Notes, client asks, cable color, GPU swap options..."
                                    className="border rounded-lg px-3 py-2 mt-3 w-full"
                                    rows="3"
                                />
                            </div>

                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <div>
                                        <p className="text-sm text-slate-500">Bill of materials</p>
                                        <h3 className="text-lg font-semibold text-slate-800">Parts & shortages</h3>
                                    </div>
                                    <div className="flex gap-2 flex-wrap">
                                        <select
                                            value={partPicker.category}
                                            onChange={(e) => {
                                                const cat = e.target.value;
                                                setPartPicker({
                                                    category: cat,
                                                    filtered: cat
                                                        ? fullInventory.filter((i) => i.typeNormalized === cat)
                                                        : fullInventory
                                                });
                                            }}
                                            className="border rounded-lg px-3 py-2 text-sm"
                                        >
                                            <option value="">Pick category</option>
                                            {['CPU', 'MOTHERBOARD', 'RAM', 'GPU', 'STORAGE', 'CPU COOLER', 'FAN', 'PSU', 'CASE', 'NETWORKING', 'PERIPHERALS'].map((c) => (
                                                <option key={c} value={c}>{c}</option>
                                            ))}
                                        </select>
                                        <select
                                            value={partSelection.inventory_id}
                                            onChange={(e) => setPartSelection({ ...partSelection, inventory_id: e.target.value })}
                                            className="border rounded-lg px-3 py-2 text-sm min-w-[240px]"
                                        >
                                            <option value="">Pick from inventory</option>
                                            {(partPicker.filtered.length ? partPicker.filtered : fullInventory).map((item) => (
                                                <option key={item.id} value={item.inventory_id}>
                                                    {item.typeNormalized} Â· {item.brand} {item.model} (qty {item.qty})
                                                </option>
                                            ))}
                                        </select>
                                        <input
                                            type="number"
                                            min="1"
                                            value={partSelection.qty}
                                            onChange={(e) => setPartSelection({ ...partSelection, qty: Number(e.target.value) })}
                                            className="w-20 border rounded-lg px-2 py-2 text-sm"
                                        />
                                        <button onClick={addPartToBuild} className="px-3 py-2 rounded-lg bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-600">
                                            Add part
                                        </button>
                                    </div>
                                </div>

                                <div className="overflow-x-auto">
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-slate-50 text-slate-600 uppercase tracking-wide text-xs">
                                            <tr>
                                                <th className="py-2 px-3 text-left">Part</th>
                                                <th className="py-2 px-3 text-left">Needed</th>
                                                <th className="py-2 px-3 text-left">Avail</th>
                                                <th className="py-2 px-3 text-left">Short</th>
                                                <th className="py-2 px-3 text-left"></th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {buildForm.parts.map((p) => {
                                                const info = shortageForPart(p.inventory_id, p.qty);
                                                return (
                                                    <tr key={p.inventory_id} className={info.missing > 0 ? 'bg-rose-50' : ''}>
                                                        <td className="py-2 px-3">
                                                            <div className="font-semibold text-slate-800">{p.label || p.inventory_id}</div>
                                                            <div className="text-xs text-slate-500">{p.inventory_id}</div>
                                                        </td>
                                                        <td className="py-2 px-3">{p.qty}</td>
                                                        <td className="py-2 px-3">{info.available}</td>
                                                        <td className="py-2 px-3 text-rose-600 font-semibold">{info.missing}</td>
                                                        <td className="py-2 px-3 text-right">
                                                            <button onClick={() => removePartFromBuild(p.inventory_id)} className="text-sm text-rose-600 underline">
                                                                Remove
                                                            </button>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                            {buildForm.parts.length === 0 && (
                                                <tr>
                                                    <td colSpan="5" className="py-4 text-center text-slate-500">
                                                        Add parts from inventory to start a bill of materials.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Build health</h4>
                                <div className="mt-2 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Parts in plan</span>
                                        <span className="font-semibold text-slate-900">{buildForm.parts.length}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Shortages</span>
                                        <span className={`px-2 py-1 rounded-lg text-sm ${buildShortageCount(buildForm.parts) > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                            {buildShortageCount(buildForm.parts) > 0 ? `${buildShortageCount(buildForm.parts)} blockers` : 'All covered'}
                                        </span>
                                    </div>
                                    {compatibilityIssues(buildForm.parts).map((issue, idx) => (
                                        <div key={idx} className="text-xs text-rose-700 bg-rose-50 border border-rose-100 rounded-lg px-2 py-1">
                                            âš ï¸ {issue}
                                        </div>
                                    ))}
                                    {buildForm.budget && (
                                        <div className="flex items-center justify-between">
                                            <span className="text-slate-700">Target budget</span>
                                            <span className="font-semibold text-slate-900">${buildForm.budget}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 max-h-[520px] overflow-y-auto">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-sm text-slate-500">Saved plans</p>
                                    <h3 className="text-lg font-semibold text-slate-800">Your builds</h3>
                                </div>
                                <div className="flex gap-2 text-xs">
                                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700">Cost & margin live</span>
                                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700">Compatibility score</span>
                                </div>
                            </div>
                                <div className="space-y-3">
                                    {builds.length === 0 && <p className="text-sm text-slate-500">No builds yet. Draft one on the left and hit Save.</p>}
                                    {builds.map((b) => {
                                        const blockers = buildShortageCount(b.parts || []);
                                        const compIssues = compatibilityIssues(b.parts || []);
                                        const score = Math.max(0, 100 - compIssues.length * 15 - blockers * 10);
                                        const cost = (b.parts || []).reduce((sum, p) => {
                                            const item = fullInventory.find((i) => i.inventory_id === p.inventory_id);
                                            return sum + (Number(item?.price_paid) || 0) * (p.qty || 1);
                                        }, 0);
                                        const sell = Number(b.budget || 0);
                                        const marginPct = sell ? Math.round(((sell - cost) / sell) * 100) : null;
                                        return (
                                            <div key={b.id} className="border border-slate-100 rounded-xl p-3 hover:border-sky-200 transition">
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="font-semibold text-slate-900">{b.name}</h4>
                                                            <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{b.status}</span>
                                                        </div>
                                                        <p className="text-xs text-slate-500">{b.client || 'Personal build'}</p>
                                                        <p className="text-xs text-slate-500">{b.parts?.length || 0} parts • {blockers} shortages • Score {score}</p>
                                                        <div className="flex flex-wrap gap-2 mt-1">
                                                            {compIssues.slice(0, 2).map((iss, idx) => (
                                                                <span key={idx} className="text-[11px] px-2 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-100">
                                                                    {iss}
                                                                </span>
                                                            ))}
                                                            {compIssues.length > 2 && <span className="text-[11px] text-rose-600">+{compIssues.length - 2} more</span>}
                                                        </div>
                                                        {sell > 0 && (
                                                            <p className={`text-xs mt-1 ${marginPct !== null && marginPct < 18 ? 'text-rose-700' : 'text-emerald-700'}`}>
                                                                Cost ${cost.toFixed(0)} • Target ${sell.toFixed(0)} • Margin {marginPct ?? 0}%
                                                                {marginPct !== null && marginPct < 18 ? ' (low)' : ''}
                                                            </p>
                                                        )}
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button onClick={() => editBuild(b)} className="text-sm text-sky-600 underline">
                                                            Open
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                const base = (b.name || 'Build').replace(/(_\d+)?$/, '');
                                                                const copies = builds
                                                                    .map((x) => x.name || '')
                                                                    .filter((n) => n.startsWith(base + '_'))
                                                                    .map((n) => parseInt((n.match(/_(\d+)$/) || [0, 0])[1], 10) || 0);
                                                                const next = copies.length ? Math.max(...copies) + 1 : 1;
                                                                const copy = { ...b, id: Date.now(), name: `${base}_${next}` };
                                                                setBuilds((prev) => [...prev, copy]);
                                                                toast('Duplicated build', true);
                                                            }}
                                                            className="text-sm text-indigo-600 underline"
                                                        >
                                                            Duplicate
                                                        </button>
                                                        <button
                                                            onClick={() => reservePartsForBuild(b)}
                                                            className="text-sm text-emerald-600 underline"
                                                        >
                                                            Reserve
                                                        </button>
                                                        <button onClick={() => exportBuildCsv(b)} className="text-sm text-emerald-600 underline">
                                                            BOM CSV
                                                        </button>
                                                        <button onClick={() => exportBuildPdf(b)} className="text-sm text-indigo-600 underline">
                                                            BOM PDF
                                                        </button>
                                                        <button onClick={() => deleteBuild(b.id)} className="text-sm text-rose-600 underline">
                                                            Delete
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'shortages' ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <StatCard title="Blockers" value={shortagesStats.blockers} accent="bg-rose-500" />
                            <StatCard title="Units missing" value={shortagesStats.unitsMissing} accent="bg-amber-500" />
                            <StatCard title="Builds affected" value={shortagesStats.buildsAffected} accent="bg-sky-500" />
                            <StatCard title="Need reorder" value={shortagesStats.needReorder} accent="bg-indigo-500" />
                        </div>

                        <div className="overflow-x-auto shadow-sm border border-gray-200 rounded-2xl bg-white">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50 text-gray-600 uppercase tracking-wide text-xs">
                                    <tr>
                                        <th className="py-3 px-4 text-left">Part</th>
                                        <th className="py-3 px-4 text-left">Needed</th>
                                        <th className="py-3 px-4 text-left">Available</th>
                                        <th className="py-3 px-4 text-left">Missing</th>
                                        <th className="py-3 px-4 text-left">Builds</th>
                                        <th className="py-3 px-4 text-left">Alternates</th>
                                        <th className="py-3 px-4 text-left"></th>
                                    </tr>
                                </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {displayShortages.map((s) => (
                                            <tr key={s.inventory_id} className="hover:bg-rose-50 transition">
                                                <td className="py-3 px-4">
                                                    <div className="font-semibold text-slate-900">{s.label}</div>
                                                    <div className="text-xs text-slate-500">{s.inventory_id}</div>
                                                </td>
                                                <td className="py-3 px-4">{s.needed || s.need || 'Missing'}</td>
                                                <td className="py-3 px-4">{s.available ?? 0}</td>
                                                <td className="py-3 px-4 text-rose-600 font-semibold">{s.missing ?? 1}</td>
                                                <td className="py-3 px-4 text-xs text-slate-600">
                                                    {(s.builds || []).join(', ') || 'â€”'}
                                                </td>
                                                <td className="py-3 px-4 text-xs text-slate-700">
                                                    {alternatesFor(s.item_type, s.inventory_id).length === 0
                                                        ? 'None on hand'
                                                        : alternatesFor(s.item_type, s.inventory_id)
                                                              .map((a) => `${a.inventory_id} (${a.qty})`)
                                                              .join(', ')}
                                                </td>
                                                <td className="py-3 px-4 text-right space-x-2">
                                                    <button
                                                        onClick={() => addRestockTask({ inventory_id: s.inventory_id, missing: s.missing ?? 1, builds: s.builds || [], reason: s.details || s.label || s.need })}
                                                        className="px-3 py-1 rounded-lg border border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100 shadow-sm"
                                                    >
                                                        Task
                                                    </button>
                                                    <button
                                                        onClick={() => markOrdered({ inventory_id: s.inventory_id, missing: s.missing ?? 1 })}
                                                        className="px-3 py-1 rounded-lg border border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 shadow-sm"
                                                    >
                                                        Order
                                                    </button>
                                                    <button
                                                        onClick={() => prefillOrderFromShortage(s)}
                                                        className="px-3 py-1 rounded-lg border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 shadow-sm"
                                                    >
                                                        Prefill PO
                                                    </button>
                                                    <button
                                                        onClick={() => setActivePage('orders')}
                                                        className="px-3 py-1 rounded-lg border border-sky-200 text-sky-700 bg-sky-50 hover:bg-sky-100 shadow-sm"
                                                    >
                                                        Go to Orders
                                                    </button>
                                                    <button
                                                        onClick={() => setActivePage('suppliers')}
                                                        className="px-3 py-1 rounded-lg border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 shadow-sm"
                                                    >
                                                        Go to Suppliers
                                                    </button>
                                                </td>
                                        </tr>
                                    ))}
                                        {displayShortages.length === 0 && (
                                            <tr>
                                                <td colSpan="7" className="py-6 text-center text-slate-500">
                                                    No shortages! All builds are covered with current stock.
                                                </td>
                                            </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {compatGaps.length > 0 && (
                            <div className="border border-amber-200 bg-amber-50 rounded-2xl p-4">
                                <div className="flex items-center gap-2 text-amber-800 font-semibold mb-2">
                                    <span>Potential compatibility gaps (from loose parts)</span>
                                </div>
                                <ul className="list-disc list-inside text-sm text-amber-900 space-y-1">
                                    {compatGaps.map((g) => (
                                        <li key={g.key}>{g.reason}</li>
                                    ))}
                                </ul>
                                <p className="text-xs text-amber-700 mt-2">These are inferred from CPUs/motherboards/RAM on hand; add matching parts or adjust sockets/DDR types.</p>
                            </div>
                        )}
                    </div>
                ) : activePage === 'picker' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <div className="xl:col-span-2 space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Financial plan</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{financialForm.id ? 'Edit plan' : 'New plan'}</h3>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setFinancialForm({ id: null, name: '', parts: [], sellPrice: '' })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">Clear</button>
                                        <button onClick={duplicateFinancialForm} className="px-3 py-2 rounded-lg border text-indigo-600 bg-white hover:bg-indigo-50 text-indigo-700 font-semibold">Duplicate</button>
                                        <button onClick={saveFinancial} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">Save</button>
                                    </div>
                                </div>
                                <input value={financialForm.name} onChange={(e) => setFinancialForm({ ...financialForm, name: e.target.value })} placeholder="Build name" className="border rounded-lg px-3 py-2 w-full mb-3" />
                                <div className="flex flex-wrap gap-2 items-center mb-3">
                                    <input value={finPart.name} onChange={(e) => setFinPart({ ...finPart, name: e.target.value })} placeholder="Part name" className="border rounded-lg px-3 py-2" />
                                    <select value={finPart.type} onChange={(e) => setFinPart({ ...finPart, type: e.target.value })} className="border rounded-lg px-3 py-2">
                                        <option value="">Part type</option>
                                        {['CPU', 'GPU', 'Motherboard', 'RAM', 'Storage', 'PSU', 'Case', 'Cooler', 'Fan', 'OS', 'Other'].map((t) => (
                                            <option key={t} value={t}>{t}</option>
                                        ))}
                                    </select>
                                    <input value={finPart.link || ''} onChange={(e) => setFinPart({ ...finPart, link: e.target.value })} placeholder="Link (Amazon/eBay etc.)" className="border rounded-lg px-3 py-2 w-60" />
                                    <input type="number" value={finPart.cost} onChange={(e) => setFinPart({ ...finPart, cost: e.target.value })} placeholder="Cost $" className="border rounded-lg px-3 py-2 w-28" />
                                    <button onClick={addFinPart} className="px-3 py-2 rounded-lg bg-emerald-500 text-white font-semibold shadow hover:bg-emerald-600">Add part</button>
                                </div>
                                <div className="space-y-1 max-h-40 overflow-y-auto border rounded-lg p-2 bg-slate-50">
                                    {financialForm.parts.length === 0 && <p className="text-sm text-slate-500">No parts added yet.</p>}
                                    {financialForm.parts.map((p, idx) => (
                                        <div key={idx} className="flex justify-between items-center text-sm gap-3">
                                            <div className="flex flex-col">
                                                <span className="font-semibold">{p.name}</span>
                                                <span className="text-[11px] text-slate-500">{p.type || 'Other'}</span>
                                                {p.link && (
                                                    <a href={p.link} target="_blank" rel="noreferrer" className="text-xs text-sky-600 underline">
                                                        Open link
                                                    </a>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold">${p.cost}</span>
                                                <button onClick={() => removeFinPart(idx)} className="text-rose-600 text-xs underline">Remove</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="p-3 rounded-lg border bg-slate-50">
                                        <p className="text-xs text-slate-500">Parts total</p>
                                        <p className="text-lg font-semibold text-slate-900">${finTotals.partsTotal.toFixed(2)}</p>
                                    </div>
                                    <div className="p-3 rounded-lg border bg-slate-50">
                                        <p className="text-xs text-slate-500">Sell price</p>
                                        <input type="number" value={financialForm.sellPrice} onChange={(e) => setFinancialForm({ ...financialForm, sellPrice: e.target.value })} className="w-full border rounded px-2 py-1 mt-1" placeholder="$" />
                                    </div>
                                    <div className="p-3 rounded-lg border bg-slate-50 col-span-2">
                                        <p className="text-xs text-slate-500">Estimated profit</p>
                                        <p className={`text-lg font-semibold ${finTotals.profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>${finTotals.profit.toFixed(2)} ({(finTotals.margin * 100).toFixed(1)}%)</p>
                                        {finTotals.margin < 0.15 && (
                                            <span className="text-xs text-amber-700 bg-amber-50 border border-amber-100 px-2 py-1 rounded">Margin below 15%</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Possible builds</h4>
                                <div className="space-y-3 mt-2">
                                    {financialBuilds.length === 0 && <p className="text-sm text-slate-500">No financial plans yet.</p>}
                                    {financialBuilds.map((b) => {
                                        const partsTotal = b.parts.reduce((s, p) => s + (Number(p.cost) || 0), 0);
                                        const profit = (Number(b.sellPrice) || 0) - partsTotal;
                                        return (
                                            <div key={b.id} className="border border-slate-100 rounded-xl p-3 hover:border-sky-200 transition">
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <div className="font-semibold text-slate-900">{b.name}</div>
                                                        <div className="text-xs text-slate-500">{b.parts.length} parts â€¢ cost ${partsTotal.toFixed(2)}</div>
                                                    </div>
                                                    <div className="text-sm font-semibold">
                                                        <span className={profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}>{profit >= 0 ? '+' : ''}${profit.toFixed(2)}</span>
                                                        <span className="text-xs text-slate-500"> ({partsTotal ? ((profit / partsTotal) * 100).toFixed(1) : '0'}%)</span>
                                                    </div>
                                                </div>
                                                <div className="text-xs text-slate-600 mt-1 space-y-1">
                                                    {b.parts.map((p, idx) => (
                                                        <div key={idx} className="flex justify-between">
                                                            <span>{p.name}</span>
                                                            <span>${p.cost}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                                <div className="flex gap-2 mt-2">
                                                    <button onClick={() => setFinancialForm(b)} className="text-sm text-sky-600 underline">Open</button>
                                                    <button onClick={() => deleteFinancial(b.id)} className="text-sm text-rose-600 underline">Delete</button>
                                                    <button
                                                        onClick={() => {
                                                            const headers = ['Part', 'Cost'];
                                                            const rows = b.parts.map((p) => [p.name, p.cost]);
                                                            const csv = [headers.join(','), ...rows.map((r) => r.join(',')), `Sell Price,${b.sellPrice}`, `Profit,${profit.toFixed(2)}`].join('\n');
                                                            const blob = new Blob([csv], { type: 'text/csv' });
                                                            const url = URL.createObjectURL(blob);
                                                            const a = document.createElement('a');
                                                            a.href = url;
                                                            a.download = `${b.name.replace(/\\s+/g, '_')}_quote.csv`;
                                                            a.click();
                                                            URL.revokeObjectURL(url);
                                                        }}
                                                        className="text-sm text-emerald-700 underline"
                                                    >
                                                        Export CSV
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'finance' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <div className="xl:col-span-2 space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Business plan</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{bizForm.id ? 'Edit period' : 'New period'}</h3>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setBizForm({ id: null, month: '', revenue: '', expenses: '', notes: '' })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">Clear</button>
                                        <button onClick={saveBizPlan} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">Save</button>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 gap-3">
                                    <input value={bizForm.month} onChange={(e) => setBizForm({ ...bizForm, month: e.target.value })} placeholder="Month / period (e.g., 2026-02)" className="border rounded-lg px-3 py-2" />
                                    <input type="number" value={bizForm.revenue} onChange={(e) => setBizForm({ ...bizForm, revenue: e.target.value })} placeholder="Projected revenue $" className="border rounded-lg px-3 py-2" />
                                    <input type="number" value={bizForm.expenses} onChange={(e) => setBizForm({ ...bizForm, expenses: e.target.value })} placeholder="Projected expenses $" className="border rounded-lg px-3 py-2" />
                                </div>
                                <textarea
                                    value={bizForm.notes}
                                    onChange={(e) => setBizForm({ ...bizForm, notes: e.target.value })}
                                    placeholder="Notes: marketing spend, hiring, big orders, risks..."
                                    className="border rounded-lg px-3 py-2 mt-3 w-full"
                                    rows="3"
                                />
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="p-3 rounded-lg border bg-slate-50">
                                        <p className="text-xs text-slate-500">Net</p>
                                        <p className={`text-lg font-semibold ${Number(bizForm.revenue || 0) - Number(bizForm.expenses || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                                            ${(Number(bizForm.revenue || 0) - Number(bizForm.expenses || 0)).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 max-h-[560px] overflow-y-auto">
                                <h4 className="text-sm text-slate-500">Financial periods</h4>
                                <div className="space-y-3 mt-2">
                                    {bizPlans.length === 0 && <p className="text-sm text-slate-500">No periods saved.</p>}
                                    {bizPlans.map((p) => {
                                        const net = (Number(p.revenue) || 0) - (Number(p.expenses) || 0);
                                        return (
                                            <div key={p.id} className="border border-slate-100 rounded-xl p-3 hover:border-sky-200 transition">
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <div className="font-semibold text-slate-900">{p.month}</div>
                                                        <div className="text-xs text-slate-500">Rev ${Number(p.revenue || 0).toFixed(2)} â€¢ Exp ${Number(p.expenses || 0).toFixed(2)}</div>
                                                    </div>
                                                    <div className={`text-sm font-semibold ${net >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                                                        {net >= 0 ? '+' : ''}${net.toFixed(2)}
                                                    </div>
                                                </div>
                                                <div className="text-xs text-slate-600 mt-1 whitespace-pre-line">{p.notes}</div>
                                                <div className="flex gap-2 mt-2">
                                                    <button onClick={() => setBizForm(p)} className="text-sm text-sky-600 underline">Open</button>
                                                    <button onClick={() => deleteBizPlan(p.id)} className="text-sm text-rose-600 underline">Delete</button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'links' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-sm text-slate-500">Social & shortcuts</p>
                                    <h3 className="text-xl font-semibold text-slate-800">Add link</h3>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => setSocialForm({ id: null, label: '', url: '', note: '' })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">Clear</button>
                                    <button onClick={saveSocial} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">Save</button>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <input value={socialForm.label} onChange={(e) => setSocialForm({ ...socialForm, label: e.target.value })} placeholder="Label (e.g., Facebook, eBay store)" className="border rounded-lg px-3 py-2 w-full" />
                                <input value={socialForm.url} onChange={(e) => setSocialForm({ ...socialForm, url: e.target.value })} placeholder="URL" className="border rounded-lg px-3 py-2 w-full" />
                                <textarea value={socialForm.note} onChange={(e) => setSocialForm({ ...socialForm, note: e.target.value })} placeholder="Notes (login, promo codes, purpose)" className="border rounded-lg px-3 py-2 w-full" rows="2" />
                            </div>
                        </div>
                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 max-h-[520px] overflow-y-auto">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-sm text-slate-500">Saved links</p>
                                    <h3 className="text-lg font-semibold text-slate-800">Quick launch</h3>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {socialLinks.length === 0 && <p className="text-sm text-slate-500">No links yet.</p>}
                                {socialLinks.map((l) => (
                                    <div key={l.id} className="border border-slate-100 rounded-lg p-3 flex items-start justify-between hover:border-sky-200 transition">
                                        <div>
                                            <div className="font-semibold text-slate-900">{l.label}</div>
                                            <div className="text-xs text-sky-700 break-all">{l.url}</div>
                                            <div className="text-xs text-slate-600">{l.note}</div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button onClick={() => window.open(l.url, '_blank')} className="text-sm text-emerald-600 underline">Open</button>
                                            <button onClick={() => setSocialForm(l)} className="text-sm text-sky-600 underline">Edit</button>
                                            <button onClick={() => deleteSocial(l.id)} className="text-sm text-rose-600 underline">Delete</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : activePage === 'autobuilder' ? (
                    <div className="space-y-4">
                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 flex flex-wrap gap-3 items-end">
                            <div>
                                <label className="text-xs text-slate-500">Socket</label>
                                <input
                                    value={autoFilters.socket}
                                    onChange={(e) => setAutoFilters({ ...autoFilters, socket: e.target.value.toUpperCase() })}
                                    placeholder="e.g., LGA1155"
                                    className="border rounded-lg px-3 py-2 w-40"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500">DDR type</label>
                                <select
                                    value={autoFilters.ddr || ''}
                                    onChange={(e) => setAutoFilters({ ...autoFilters, ddr: e.target.value })}
                                    className="border rounded-lg px-3 py-2 w-32"
                                >
                                    <option value="">Any</option>
                                    <option value="DDR3">DDR3</option>
                                    <option value="DDR4">DDR4</option>
                                    <option value="DDR5">DDR5</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs text-slate-500">Min PSU watts</label>
                                <input
                                    type="number"
                                    min="0"
                                    value={autoFilters.minPsu}
                                    onChange={(e) => setAutoFilters({ ...autoFilters, minPsu: Number(e.target.value) || 0 })}
                                    className="border rounded-lg px-3 py-2 w-32"
                                />
                            </div>
                            <button onClick={() => setAutoFilters({ socket: '', ddr: '', minPsu: 0 })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">
                                Clear
                            </button>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div>
                                        <p className="text-xs uppercase tracking-wide text-slate-500">Auto-built</p>
                                        <h3 className="text-lg font-semibold text-slate-900">Complete builds</h3>
                                    </div>
                                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                                        {autoBuilds.complete.length} ready
                                    </span>
                                </div>
                                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                                    {autoBuilds.complete.length === 0 && <p className="text-sm text-slate-500">No complete builds yet.</p>}
                                    {autoBuilds.complete.map((b) => {
                                        const partsArr = [
                                            { inventory_id: b.cpu.inventory_id, qty: 1 },
                                            b.motherboard && { inventory_id: b.motherboard.inventory_id, qty: 1 },
                                            b.ram && { inventory_id: b.ram.inventory_id, qty: 1 },
                                            b.psu && { inventory_id: b.psu.inventory_id, qty: 1 },
                                            b.gpu && { inventory_id: b.gpu.inventory_id, qty: 1 },
                                            b.case && { inventory_id: b.case.inventory_id, qty: 1 },
                                            b.cooler && { inventory_id: b.cooler.inventory_id, qty: 1 },
                                            b.storage && { inventory_id: b.storage.inventory_id, qty: 1 },
                                            b.fan && { inventory_id: b.fan.inventory_id, qty: 1 }
                                        ].filter(Boolean);
                                        const issues = compatibilityIssues(partsArr);
                                        const score = Math.max(0, 100 - issues.length * 15);
                                        const cost = costForParts(partsArr);
                                        return (
                                            <div key={b.id} className="border border-slate-100 rounded-xl p-3 hover:border-sky-200 transition">
                                                <div className="flex items-center justify-between">
                                                    <div className="text-sm font-semibold text-slate-900">{b.cpu.model}</div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">Socket {b.socket}</span>
                                                        <span className={`text-xs px-2 py-1 rounded-full ${score >= 80 ? 'bg-emerald-100 text-emerald-700' : score >= 60 ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'}`}>
                                                            Score {score}
                                                        </span>
                                                    </div>
                                                </div>
                                                <ul className="text-xs text-slate-700 mt-2 space-y-1">
                                                    <li>MB: {b.motherboard?.model || '—'}</li>
                                                    <li>RAM: {b.ram?.model || '—'} {b.ddr && `(${b.ddr})`}</li>
                                                    <li>PSU: {b.psu?.model || '—'}</li>
                                                    <li>GPU: {b.gpu?.model || 'Optional/none'}</li>
                                                    <li>Case: {b.case?.model || 'Optional/none'}</li>
                                                    <li>Cooler: {b.cooler?.model || 'Optional/none'}</li>
                                                </ul>
                                                {issues.length > 0 && (
                                                    <div className="mt-2 text-[11px] text-rose-700 flex flex-wrap gap-1">
                                                        {issues.slice(0, 3).map((iss, idx) => (
                                                            <span key={idx} className="px-2 py-1 rounded-full bg-rose-50 border border-rose-100">{iss}</span>
                                                        ))}
                                                    </div>
                                                )}
                                                <div className="text-[11px] text-slate-700 mt-2">Est. cost: ${cost.toFixed(0)}</div>
                                                <div className="mt-2 flex gap-2 text-[11px] text-slate-700">
                                                    <button
                                                        onClick={() => exportBuildCsv({ name: `${b.cpu.model}-${b.socket}`, parts: partsArr })}
                                                        className="px-2 py-1 rounded border border-slate-200 bg-white hover:border-sky-200"
                                                    >
                                                        Export BOM
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="bg-white border border-amber-200 rounded-2xl shadow-sm p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div>
                                        <p className="text-xs uppercase tracking-wide text-amber-700">Gaps</p>
                                        <h3 className="text-lg font-semibold text-slate-900">Partial builds</h3>
                                    </div>
                                    <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                                        {autoBuilds.partial.length} partial
                                    </span>
                                </div>
                                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                                    {autoBuilds.partial.length === 0 && <p className="text-sm text-slate-500">No partials.</p>}
                                    {autoBuilds.partial.map((b) => (
                                        <div key={b.id} className="border border-amber-100 rounded-xl p-3 bg-amber-50/40">
                                            <div className="flex items-center justify-between">
                                                <div className="text-sm font-semibold text-slate-900">{b.cpu.model}</div>
                                                <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                                                    Missing {b.missing.length}
                                                </span>
                                            </div>
                                            <ul className="text-xs text-slate-700 mt-2 space-y-1">
                                                <li>MB: {b.motherboard?.model || '—'}</li>
                                                <li>RAM: {b.ram?.model || '—'}</li>
                                                <li>PSU: {b.psu?.model || '—'}</li>
                                                <li className="text-amber-800 font-semibold">Need: {b.missing.join(', ')}</li>
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {autoBuilds.missing.length > 0 && (
                            <div className="bg-white border border-rose-200 rounded-2xl shadow-sm p-4">
                                <h4 className="text-sm font-semibold text-rose-700 mb-1">Missing everything</h4>
                                <p className="text-xs text-rose-600">{autoBuilds.missing.join('; ')}</p>
                            </div>
                        )}
                    </div>
                ) : activePage === 'about' ? (
                    <div className="grid grid-cols-1 gap-4">
                        <div className="grid md:grid-cols-3 gap-4">
                            <div className="md:col-span-2 bg-white border border-gray-200 rounded-2xl shadow-sm p-5 space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs uppercase tracking-wide text-slate-500">Dashboard</p>
                                        <h3 className="text-2xl font-bold text-slate-900">About WhatAPC</h3>
                                        <p className="text-sm text-slate-600">Strategic view of the business, hardware philosophy, and operating playbook.</p>
                                    </div>
                                    <div className="hidden sm:flex gap-2">
                                        {[
                                            { id: 'overview', label: 'Overview' },
                                            { id: 'flagship', label: 'Flagship build' },
                                            { id: 'forever', label: 'Forever PC' },
                                            { id: 'timeline', label: 'Milestones' }
                                        ].map((b) => (
                                            <a key={b.id} href={`#${b.id}`} className="px-3 py-2 text-xs font-semibold rounded-full bg-sky-50 text-sky-700 border border-sky-100 hover:bg-sky-100">
                                                {b.label}
                                            </a>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    <span className="px-2 py-1 text-xs rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">Forever PC</span>
                                    <span className="px-2 py-1 text-xs rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">Sustainable hardware</span>
                                    <span className="px-2 py-1 text-xs rounded-full bg-amber-50 text-amber-700 border border-amber-100">Service-first</span>
                                    <span className="px-2 py-1 text-xs rounded-full bg-rose-50 text-rose-700 border border-rose-100">Community impact</span>
                                </div>
                            </div>
                            <div className="relative overflow-hidden rounded-2xl shadow-sm bg-gradient-to-br from-sky-500 to-indigo-600 text-white border border-indigo-300/40 min-h-[140px]">
                                <img
                                    src="/whatapc-hero-new.png"
                                    alt="WhatAPC visual"
                                    className="absolute inset-0 w-full h-full object-cover"
                                    onError={(e) => {
                                        e.currentTarget.onerror = null;
                                        e.currentTarget.src = '/whatapc_banner.jpg';
                                    }}
                                />
                                <div className="absolute inset-0 bg-slate-900/10" />
                            </div>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 space-y-6 max-h-[70vh] overflow-y-auto">
                            <section id="overview" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Overview</h4>
                                <p className="text-sm text-slate-700">WhatAPC balances enthusiast-grade legacy hardware with modern service delivery. The goal: machines that act like assets, not consumables, and can evolve for years.</p>
                            </section>

                            <section id="flagship" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Flagship "Ultimate Gaming Computer"</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>CPU: Intel Core i7-8700K (often 4.9 GHz OC)</li>
                                    <li>GPU: Dual GTX 1080 Ti SLI (22GB GDDR5X mirrored)</li>
                                    <li>RAM: 32GB DDR4; Storage: 250GB SSD + bulk HDD</li>
                                    <li>Delivery cycles extend into late 2025; communicated up front.</li>
                                </ul>
                            </section>

                            <section id="forever" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Forever PC pillars</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>ATX tower with clearance for future GPUs; 5.25" bay when possible.</li>
                                    <li>Robust VRMs, 4+ DIMM slots, multiple M.2 for long-term growth.</li>
                                    <li>Efficiency over heat: prefer balanced CPUs (Ryzen 7 5800X / i5-12600K) vs 240W extremes.</li>
                                </ul>
                            </section>

                            <section id="supply" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Supply & Fulfillment</h4>
                                <p className="text-sm text-slate-700">Just-in-time ordering to avoid depreciating stock; transparent timelines and tracking to keep buyers informed.</p>
                                <p className="text-sm text-slate-700">Used/secondary market angles: RTX 2080 Ti ($270-$400) and Xeon E5-2670 v2 deliver strong value; i7-8700K balances single-thread performance.</p>
                            </section>

                            <section id="services" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Services & Profitability</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>Data recovery tiers: logical $100-$600; physical $400-$2,000+; RAID $1,500-$10k.</li>
                                    <li>Labor benchmarks: tech pay ~$18-$20/hr; billable $75-$200/hr by complexity.</li>
                                    <li>Shift 45-65% of clients to monitoring subscriptions for stable cash flow.</li>
                                </ul>
                            </section>

                            <section id="legal" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Legal & Policy</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>Operate as LLC; carry at least $1M general liability.</li>
                                    <li>50% non-refundable deposit before ordering parts (clearly defined as liquidated damages).</li>
                                </ul>
                            </section>

                            <section id="digital" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Digital roadmap</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>Compatibility checker, AR/3D visualization, AI chatbot support.</li>
                                    <li>Role-based client portal for invoices, build status, and support.</li>
                                    <li>Real-time GPU alerts; build logs and videos as educational marketing.</li>
                                </ul>
                            </section>

                            <section id="social" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Social responsibility</h4>
                                <p className="text-sm text-slate-700">Youth PC-building workshops (pre-mount CPUs; let students install RAM/storage). Donation program follows NIST 800-88 purge, R2 recycling, 501(c)3 eligibility, and IRS Form 8283 documentation.</p>
                            </section>

                            <section id="timeline" className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Timeline & milestones</h4>
                                <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
                                    <li>Q1 2025: Launch Forever PC positioning and compatibility checker.</li>
                                    <li>Q2 2025: Add monitoring subscriptions; formalize 50% deposit policy.</li>
                                    <li>Q3 2025: Publish build logs/AR previews; expand data recovery tiering.</li>
                                    <li>Q4 2025: Community workshops and donation program roll-out.</li>
                                    <li>2026: Grow supplier network, tighten JIT logistics, refresh flagship SKUs.</li>
                                </ul>
                            </section>

                            <section className="space-y-2">
                                <h4 className="text-lg font-semibold text-slate-900">Synthesis</h4>
                                <p className="text-sm text-slate-700">WhatAPC aims to be a sustainable, high-performance builder: Forever PC philosophy, solid legal/payment footing, advanced configurators, and community impact through education and responsible reuse.</p>
                            </section>
                        </div>
                    </div>
                ) : activePage === 'orders' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <div className="xl:col-span-2 space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Purchase order</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{orderForm.id ? 'Edit order' : 'New order'}</h3>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setOrderForm({ id: null, vendor: '', channel: '', status: 'Draft', total: '', due_date: '', tracking: '', items: '', notes: '' })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">
                                            Clear
                                        </button>
                                        <button onClick={saveOrder} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">
                                            Save order
                                        </button>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 gap-3">
                                    <input name="vendor" value={orderForm.vendor} onChange={(e) => setOrderForm({ ...orderForm, vendor: e.target.value })} placeholder="Vendor (e.g., seller123, Amazon)" className="border rounded-lg px-3 py-2" />
                                    <input name="channel" value={orderForm.channel} onChange={(e) => setOrderForm({ ...orderForm, channel: e.target.value })} placeholder="Channel (eBay, Direct, Distributor)" className="border rounded-lg px-3 py-2" />
                                    <select name="status" value={orderForm.status} onChange={(e) => setOrderForm({ ...orderForm, status: e.target.value })} className="border rounded-lg px-3 py-2">
                                        <option>Draft</option>
                                        <option>Quoted</option>
                                        <option>Ordered</option>
                                        <option>Shipped</option>
                                        <option>Delivered</option>
                                        <option>Closed</option>
                                    </select>
                                    <input name="total" type="number" step="0.01" value={orderForm.total} onChange={(e) => setOrderForm({ ...orderForm, total: e.target.value })} placeholder="Total $" className="border rounded-lg px-3 py-2" />
                                    <input name="due_date" type="date" value={orderForm.due_date} onChange={(e) => setOrderForm({ ...orderForm, due_date: e.target.value })} className="border rounded-lg px-3 py-2" />
                                    <input name="tracking" value={orderForm.tracking} onChange={(e) => setOrderForm({ ...orderForm, tracking: e.target.value })} placeholder="Tracking / PO #" className="border rounded-lg px-3 py-2" />
                                </div>
                                <textarea
                                    name="items"
                                    value={orderForm.items}
                                    onChange={(e) => setOrderForm({ ...orderForm, items: e.target.value })}
                                    placeholder="Line items (paste part numbers, SKUs, qty)â€¦"
                                    className="border rounded-lg px-3 py-2 mt-3 w-full"
                                    rows="3"
                                />
                                <textarea
                                    name="notes"
                                    value={orderForm.notes}
                                    onChange={(e) => setOrderForm({ ...orderForm, notes: e.target.value })}
                                    placeholder="Payment terms, tax, shipping speed, RMA detailsâ€¦"
                                    className="border rounded-lg px-3 py-2 mt-3 w-full"
                                    rows="2"
                                />
                            </div>

                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 overflow-x-auto">
                                <table className="min-w-full text-sm">
                                    <thead className="bg-slate-50 text-slate-600 uppercase tracking-wide text-xs">
                                        <tr>
                                            <th className="py-2 px-3 text-left">Vendor</th>
                                            <th className="py-2 px-3 text-left">Status</th>
                                            <th className="py-2 px-3 text-left">Total</th>
                                            <th className="py-2 px-3 text-left">Due / ETA</th>
                                            <th className="py-2 px-3 text-left">Tracking</th>
                                            <th className="py-2 px-3 text-left">Items</th>
                                            <th className="py-2 px-3 text-left"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {orders.map((o) => (
                                            <tr key={o.id} className="hover:bg-sky-50 transition">
                                                <td className="py-2 px-3">
                                                    <div className="font-semibold text-slate-900">{o.vendor}</div>
                                                    <div className="text-xs text-slate-500">{o.channel}</div>
                                                </td>
                                                <td className="py-2 px-3">
                                                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700 text-xs">{o.status}</span>
                                                </td>
                                                <td className="py-2 px-3">${o.total || 'â€”'}</td>
                                                <td className="py-2 px-3 text-xs text-slate-600">{o.due_date || 'â€”'}</td>
                                                <td className="py-2 px-3 text-xs text-slate-600">{o.tracking || 'â€”'}</td>
                                                <td className="py-2 px-3 text-xs text-slate-700 max-w-xs whitespace-pre-line">{o.items}</td>
                                                <td className="py-2 px-3 text-right space-x-2">
                                                    <button onClick={() => editOrder(o)} className="text-sm text-sky-600 underline">Open</button>
                                                    <button onClick={() => deleteOrder(o.id)} className="text-sm text-rose-600 underline">Delete</button>
                                                </td>
                                            </tr>
                                        ))}
                                        {orders.length === 0 && (
                                            <tr>
                                                <td colSpan="7" className="py-4 text-center text-slate-500">No orders yet. Create one on the left.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Order stats</h4>
                                <div className="mt-2 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Open orders</span>
                                        <span className="font-semibold text-slate-900">{orders.filter((o) => o.status !== 'Delivered' && o.status !== 'Closed').length}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Total spend (open)</span>
                                        <span className="font-semibold text-slate-900">
                                            $
                                            {orders
                                                .filter((o) => o.status !== 'Delivered' && o.status !== 'Closed')
                                                .reduce((s, o) => s + Number(o.total || 0), 0)
                                                .toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Awaiting tracking</span>
                                        <span className="font-semibold text-slate-900">{orders.filter((o) => !o.tracking).length}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Quick fill</h4>
                                <div className="space-y-2 text-sm text-slate-700">
                                    <p>â€¢ Paste SKUs/links into Items and set status to â€œOrderedâ€.</p>
                                    <p>â€¢ Use â€œShippedâ€ when you add tracking; â€œDeliveredâ€ auto-clears from open spend.</p>
                                    <p>â€¢ Vendor field pairs nicely with suppliers you saved.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'tasks' ? (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <div className="xl:col-span-2 space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-slate-500">Task</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{taskForm.id ? 'Edit task' : 'New task'}</h3>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setTaskForm({ id: null, title: '', category: 'General', status: 'Open', priority: 'Normal', due_date: '', notes: '' })}
                                            className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50"
                                        >
                                            Clear
                                        </button>
                                        <button onClick={saveTask} className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600">
                                            Save task
                                        </button>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 gap-3">
                                    <input name="title" value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} placeholder="Task title" className="border rounded-lg px-3 py-2" />
                                    <input name="due_date" type="date" value={taskForm.due_date} onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })} className="border rounded-lg px-3 py-2" />
                                    <select name="category" value={taskForm.category} onChange={(e) => setTaskForm({ ...taskForm, category: e.target.value })} className="border rounded-lg px-3 py-2">
                                        <option>General</option>
                                        <option>Restock</option>
                                        <option>Order</option>
                                        <option>Build</option>
                                        <option>Customer</option>
                                    </select>
                                    <select name="priority" value={taskForm.priority} onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })} className="border rounded-lg px-3 py-2">
                                        <option>Low</option>
                                        <option>Normal</option>
                                        <option>High</option>
                                        <option>Urgent</option>
                                    </select>
                                    <select name="status" value={taskForm.status} onChange={(e) => setTaskForm({ ...taskForm, status: e.target.value })} className="border rounded-lg px-3 py-2">
                                        <option>Open</option>
                                        <option>In Progress</option>
                                        <option>Blocked</option>
                                        <option>Done</option>
                                    </select>
                                </div>
                                <textarea
                                    name="notes"
                                    value={taskForm.notes}
                                    onChange={(e) => setTaskForm({ ...taskForm, notes: e.target.value })}
                                    placeholder="Details, links, what to verifyâ€¦"
                                    className="border rounded-lg px-3 py-2 mt-3 w-full"
                                    rows="3"
                                />
                            </div>

                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 overflow-x-auto">
                                <table className="min-w-full text-sm">
                                    <thead className="bg-slate-50 text-slate-600 uppercase tracking-wide text-xs">
                                        <tr>
                                            <th className="py-2 px-3 text-left">Title</th>
                                            <th className="py-2 px-3 text-left">Category</th>
                                            <th className="py-2 px-3 text-left">Priority</th>
                                            <th className="py-2 px-3 text-left">Status</th>
                                            <th className="py-2 px-3 text-left">Due</th>
                                            <th className="py-2 px-3 text-left">Notes</th>
                                            <th className="py-2 px-3 text-left"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {tasks.map((t) => (
                                            <tr key={t.id} className="hover:bg-sky-50 transition">
                                                <td className="py-2 px-3">
                                                    <div className="font-semibold text-slate-900">{t.title}</div>
                                                    <div className="text-xs text-slate-500">{t.created_at}</div>
                                                </td>
                                                <td className="py-2 px-3 text-xs text-slate-600">{t.category}</td>
                                                <td className="py-2 px-3 text-xs">
                                                    <span className="px-2 py-1 rounded-full bg-amber-50 text-amber-700">{t.priority}</span>
                                                </td>
                                                <td className="py-2 px-3 text-xs">
                                                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700">{t.status}</span>
                                                </td>
                                                <td className="py-2 px-3 text-xs text-slate-600">{t.due_date || 'â€”'}</td>
                                                <td className="py-2 px-3 text-xs text-slate-700 max-w-xs whitespace-pre-line">{t.notes}</td>
                                                <td className="py-2 px-3 text-right space-x-2">
                                                    <button onClick={() => editTask(t)} className="text-sm text-sky-600 underline">Open</button>
                                                    <button onClick={() => deleteTask(t.id)} className="text-sm text-rose-600 underline">Delete</button>
                                                </td>
                                            </tr>
                                        ))}
                                        {tasks.length === 0 && (
                                            <tr>
                                                <td colSpan="7" className="py-4 text-center text-slate-500">No tasks yet. Add one on the left or from Shortages.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Task stats</h4>
                                <div className="mt-2 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Open</span>
                                        <span className="font-semibold text-slate-900">{tasks.filter((t) => t.status !== 'Done').length}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">High/Urgent</span>
                                        <span className="font-semibold text-slate-900">{tasks.filter((t) => t.priority === 'High' || t.priority === 'Urgent').length}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-700">Due today/overdue</span>
                                        <span className="font-semibold text-slate-900">
                                            {tasks.filter((t) => {
                                                if (!t.due_date) return false;
                                                return new Date(t.due_date) <= new Date();
                                            }).length}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                <h4 className="text-sm text-slate-500">Quick tips</h4>
                                <div className="space-y-2 text-sm text-slate-700">
                                    <p>â€¢ Restock/Ordered buttons auto-log tasks here.</p>
                                    <p>â€¢ Use categories to cluster (Restock, Build, Customer).</p>
                                    <p>â€¢ Mark status â€œDoneâ€ to keep board clean.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'profit' ? (
                    <div className="space-y-4 w-full">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                            <StatCard title="Capital velocity" value={`$${profitEngine.capitalVelocity.toFixed(1)}/day`} accent="bg-indigo-500" />
                            <StatCard title="Top item ROI/day" value={profitEngine.topItems[0] ? `$${profitEngine.topItems[0].profitPerDay.toFixed(1)}` : '$0'} accent="bg-emerald-500" />
                            <StatCard title="Best build ROI" value={profitEngine.bestBuild ? `${profitEngine.bestBuild.roi.toFixed(0)}%` : '—'} accent="bg-amber-500" />
                            <StatCard title="Inventory count" value={profitEngine.items.length} accent="bg-slate-500" />
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold text-slate-800">Today’s best move</h4>
                                {profitEngine.bestBuild && (
                                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">Build-first</span>
                                )}
                            </div>
                            {profitEngine.bestBuild ? (
                                <div className="text-sm text-slate-800">
                                    Build: {profitEngine.bestBuild.build.name || profitEngine.bestBuild.build.id} • Expected profit ${profitEngine.bestBuild.profit.toFixed(0)} • ROI {profitEngine.bestBuild.roi.toFixed(0)}%
                                    {profitEngine.bestBuild.issues?.length ? (
                                        <div className="text-[11px] text-rose-700 mt-1">Needs: {profitEngine.bestBuild.issues.slice(0, 3).join(', ')}</div>
                                    ) : (
                                        <div className="text-[11px] text-emerald-700 mt-1">Ready to assemble.</div>
                                    )}
                                </div>
                            ) : (
                                <p className="text-sm text-slate-500">No build stands out yet.</p>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 h-full">
                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Top items by profit/day</h4>
                                <div className="space-y-2 text-sm">
                                    {profitEngine.topItems.length === 0 && <p className="text-slate-500">No data.</p>}
                                    {profitEngine.topItems.map((t) => (
                                        <div key={t.item.inventory_id} className="flex justify-between">
                                            <div>
                                                <div className="font-semibold text-slate-900">{t.item.model || t.item.inventory_id}</div>
                                                <div className="text-[11px] text-slate-500">{t.item.typeNormalized} • ROI {t.roi.toFixed(0)}%</div>
                                            </div>
                                            <div className="text-emerald-700 font-semibold">${t.profitPerDay.toFixed(1)}/day</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 h-full">
                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Decision cues</h4>
                                <ul className="text-sm text-slate-700 space-y-1">
                                    <li>🟢 BUILD NOW: ROI &gt; 40% and missing ≤ 1 cheap part.</li>
                                    <li>🟡 HOLD: market trending up or waiting on GPU/CPU.</li>
                                    <li>🔴 PART OUT: ROI &lt; 20% or days held &gt; 60.</li>
                                    <li>🔥 PRIORITY LIST: highest profit/day first.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                ) : activePage === 'ops' ? (
                    <div className="space-y-4 w-full">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 flex-1">
                                <StatCard title="Orders (all)" value={`$${opsStats.orderSpend.toFixed(0)}`} accent="bg-indigo-500" />
                                <StatCard title="Delivered spend" value={`$${opsStats.deliveredSpend.toFixed(0)}`} accent="bg-emerald-500" />
                                <StatCard title="Deal revenue" value={`$${opsStats.dealRevenue.toFixed(0)}`} accent="bg-sky-500" />
                                <StatCard title="Avg margin" value={`${opsStats.dealMargin}%`} accent="bg-amber-500" />
                            </div>
                            <div className="md:ml-4">
                                <label className="text-xs text-slate-600 block mb-1">Range</label>
                                <select value={opsRange} onChange={(e) => setOpsRange(e.target.value)} className="border rounded-lg px-2 py-1 text-sm">
                                    <option value="all">All time</option>
                                    <option value="30">Last 30 days</option>
                                    <option value="90">Last 90 days</option>
                                </select>
                            </div>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold text-slate-800">What to order</h4>
                                <span className="text-xs text-slate-500">{orderSuggestions.length} needs</span>
                            </div>
                            <div className="divide-y divide-slate-100">
                                {orderSuggestions.length === 0 && <p className="text-sm text-slate-500 p-2">No shortages.</p>}
                                {orderSuggestions.map((s) => {
                                    const bestSup = suppliers
                                        .map((sup) => {
                                            const orderCount = orders.filter((o) => o.vendor === sup.name).length;
                                            const delivered = orders.filter((o) => o.vendor === sup.name && o.status === 'Delivered').length;
                                            const sla = orderCount ? delivered / orderCount : 0;
                                            return { sup, sla };
                                        })
                                        .sort((a, b) => b.sla - a.sla)[0];
                                    return (
                                        <div key={s.inventory_id} className="py-2 flex items-center justify-between">
                                            <div>
                                                <div className="text-sm font-semibold text-slate-900">{s.label}</div>
                                                <div className="text-xs text-slate-600">Need {s.missing} • Type {s.item_type}</div>
                                                {bestSup && (
                                                    <div className="text-[11px] text-slate-500">Try: {bestSup.sup.name} (SLA {(bestSup.sla * 100).toFixed(0)}%)</div>
                                                )}
                                            </div>
                                            <div className="flex gap-2 text-xs">
                                                <button onClick={() => prefillOrderFromShortage(s)} className="px-2 py-1 rounded border bg-white hover:border-sky-200">Prefill PO</button>
                                                <button onClick={() => addRestockTask({ inventory_id: s.inventory_id, missing: s.missing, builds: s.builds || [], reason: s.label })} className="px-2 py-1 rounded border bg-white hover:border-amber-200">Task</button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold text-slate-800">Profit quick look</h4>
                                <span className="text-xs text-slate-500">{deals.length} deals</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {deals.length === 0 && <p className="text-sm text-slate-500">No deals yet.</p>}
                                {deals.map((d) => {
                                    const build = builds.find((b) => b.id === d.buildId);
                                    const cost = costForParts(build?.parts || []);
                                    const sell = Number(d.amount || 0);
                                    const margin = sell ? Math.round(((sell - cost) / sell) * 100) : 0;
                                    return (
                                        <div key={d.id} className="border border-slate-100 rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <div className="font-semibold text-slate-900">{d.name}</div>
                                                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{d.stage}</span>
                                            </div>
                                            <div className="text-xs text-slate-600">{d.client || 'No client'} • ${sell.toFixed(0)}</div>
                                            <div className={`text-xs mt-1 ${margin < 18 ? 'text-rose-700' : 'text-emerald-700'}`}>Margin {margin}% (cost ${cost.toFixed(0)})</div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4 w-full">
                        {navItems.filter((n) => n.id === activePage).map((n) => (
                            <div key={n.id} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 w-full">
                                <div className="flex items-center gap-3 mb-3">
                                    <span className="text-2xl">{n.icon}</span>
                                    <div>
                                        <p className="text-sm text-slate-500">Page</p>
                                        <h3 className="text-xl font-semibold text-slate-800">{n.label}</h3>
                                    </div>
                                </div>
                                <p className="text-slate-600 mb-3">{n.blurb}</p>
                                {n.id === 'suppliers' ? (
                                    <div className="space-y-3">
                                        <form className="space-y-2" onSubmit={addSupplier}>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                <input name="name" value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} placeholder="Supplier / store name" className="border rounded-lg px-3 py-2 text-sm" />
                                                <input name="channel" value={supplierForm.channel} onChange={(e) => setSupplierForm({ ...supplierForm, channel: e.target.value })} placeholder="Channel (eBay, Amazon, site)" className="border rounded-lg px-3 py-2 text-sm" />
                                            </div>
                                            <input name="website" value={supplierForm.website} onChange={(e) => setSupplierForm({ ...supplierForm, website: e.target.value })} placeholder="Website or profile URL" className="border rounded-lg px-3 py-2 text-sm w-full" />
                                            <input name="contact" value={supplierForm.contact} onChange={(e) => setSupplierForm({ ...supplierForm, contact: e.target.value })} placeholder="Contact / handle" className="border rounded-lg px-3 py-2 text-sm w-full" />
                                            <textarea name="preferred_items" value={supplierForm.preferred_items} onChange={(e) => setSupplierForm({ ...supplierForm, preferred_items: e.target.value })} placeholder="Preferred SKUs (e.g., Noctua fans, 80+ Gold PSUs)" className="border rounded-lg px-3 py-2 text-sm w-full" rows="2" />
                                            <textarea name="notes" value={supplierForm.notes} onChange={(e) => setSupplierForm({ ...supplierForm, notes: e.target.value })} placeholder="Shipping speed, RMA policy, coupon codes..." className="border rounded-lg px-3 py-2 text-sm w-full" rows="2" />
                                            <div className="flex justify-end">
                                                <button type="submit" className="px-3 py-2 rounded-lg bg-sky-500 text-white text-sm font-semibold shadow hover:bg-sky-600">Add supplier</button>
                                            </div>
                                        </form>
                                        <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl">
                                            {suppliers.length === 0 && <p className="p-3 text-sm text-slate-500">No suppliers yet. Add your favorite eBay sellers or sites above.</p>}
                                            {suppliers
                                                .map((s) => {
                                                    const orderCount = orders.filter((o) => o.vendor === s.name).length;
                                                    const delivered = orders.filter((o) => o.vendor === s.name && o.status === 'Delivered').length;
                                                    const sla = orderCount ? Math.round((delivered / orderCount) * 100) : 0;
                                                    return { ...s, orderCount, delivered, sla };
                                                })
                                                .sort((a, b) => b.sla - a.sla)
                                                .map((s) => (
                                                    <div key={s.id} className="p-3 space-y-1">
                                                        <div className="flex items-center justify-between">
                                                            <div className="font-semibold text-slate-900">{s.name}</div>
                                                            <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{s.channel || 'Supplier'}</span>
                                                        </div>
                                                        <div className="text-xs text-slate-600">{s.website}</div>
                                                        <div className="text-xs text-slate-600">{s.contact}</div>
                                                        <div className="text-xs text-slate-600">Prefers: {s.preferred_items || '—'}</div>
                                                        <div className="text-xs text-slate-600">Orders: {s.orderCount} • Delivered: {s.delivered} • SLA: {s.sla}%</div>
                                                        <div className="text-xs text-slate-500">{s.notes}</div>
                                                    </div>
                                                ))}
                                        </div>
                                    </div>
                                ) : n.id === 'sales' ? (
                                    <div className="space-y-4">
                                        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                                            <div className="flex items-center justify-between mb-3">
                                                <div>
                                                    <p className="text-xs text-slate-500 uppercase">Deal</p>
                                                    <h3 className="text-lg font-semibold text-slate-800">{dealForm.id ? 'Edit deal' : 'New deal'}</h3>
                                                </div>
                                                <div className="flex gap-2">
                                                    <button onClick={() => setDealForm({ id: null, name: '', client: '', buildId: '', amount: '', stage: 'Lead', status: 'Open', due_date: '', notes: '' })} className="px-2 py-1 text-sm border rounded bg-white">Clear</button>
                                                    <button onClick={() => {
                                                        if (!dealForm.name.trim()) return alert('Deal name required');
                                                        const payload = { ...dealForm, id: dealForm.id || Date.now() };
                                                        setDeals((prev) => {
                                                            const exists = prev.find((d) => d.id === payload.id);
                                                            if (exists) return prev.map((d) => d.id === payload.id ? payload : d);
                                                            return [...prev, payload];
                                                        });
                                                        setDealForm({ id: null, name: '', client: '', buildId: '', amount: '', stage: 'Lead', status: 'Open', due_date: '', notes: '' });
                                                    }} className="px-2 py-1 text-sm rounded bg-sky-500 text-white">Save</button>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                <input value={dealForm.name} onChange={(e) => setDealForm({ ...dealForm, name: e.target.value })} placeholder="Deal name" className="border rounded px-3 py-2 text-sm" />
                                                <input value={dealForm.client} onChange={(e) => setDealForm({ ...dealForm, client: e.target.value })} placeholder="Client" className="border rounded px-3 py-2 text-sm" />
                                                <select value={dealForm.buildId} onChange={(e) => setDealForm({ ...dealForm, buildId: e.target.value })} className="border rounded px-3 py-2 text-sm">
                                                    <option value="">Link build (optional)</option>
                                                    {builds.map((b) => (
                                                        <option key={b.id} value={b.id}>{b.name}</option>
                                                    ))}
                                                </select>
                                                <input type="number" value={dealForm.amount} onChange={(e) => setDealForm({ ...dealForm, amount: e.target.value })} placeholder="Sell price" className="border rounded px-3 py-2 text-sm" />
                                                <select value={dealForm.stage} onChange={(e) => setDealForm({ ...dealForm, stage: e.target.value })} className="border rounded px-3 py-2 text-sm">
                                                    {['Lead', 'Quote', 'Negotiation', 'Won', 'Lost'].map((s) => <option key={s}>{s}</option>)}
                                                </select>
                                                <select value={dealForm.status} onChange={(e) => setDealForm({ ...dealForm, status: e.target.value })} className="border rounded px-3 py-2 text-sm">
                                                    {['Open', 'Closed'].map((s) => <option key={s}>{s}</option>)}
                                                </select>
                                                <input type="date" value={dealForm.due_date} onChange={(e) => setDealForm({ ...dealForm, due_date: e.target.value })} className="border rounded px-3 py-2 text-sm" />
                                            </div>
                                            <textarea value={dealForm.notes} onChange={(e) => setDealForm({ ...dealForm, notes: e.target.value })} placeholder="Notes" className="border rounded px-3 py-2 text-sm w-full mt-2" rows="2" />
                                        </div>

                                        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                                            <div className="flex items-center justify-between mb-3">
                                                <div>
                                                    <p className="text-xs uppercase text-slate-500">Pipeline</p>
                                                    <h3 className="text-lg font-semibold text-slate-800">Deals</h3>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                                {deals.length === 0 && <p className="text-sm text-slate-500">No deals yet.</p>}
                                                {deals.map((d) => {
                                                    const build = builds.find((b) => b.id === d.buildId);
                                                    const partsArr = build?.parts || [];
                                                    const cost = costForParts(partsArr);
                                                    const sell = Number(d.amount || 0);
                                                    const marginPct = sell ? Math.round(((sell - cost) / sell) * 100) : 0;
                                                    return (
                                                        <div key={d.id} className="border border-slate-100 rounded-lg p-3 shadow-sm bg-white">
                                                            <div className="flex items-center justify-between">
                                                                <div className="font-semibold text-slate-900">{d.name}</div>
                                                                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{d.stage}</span>
                                                            </div>
                                                            <div className="text-xs text-slate-600">{d.client || 'No client'}</div>
                                                            <div className="text-sm font-semibold mt-1">${sell.toFixed(0)}</div>
                                                            {build && <div className="text-[11px] text-slate-600">Build: {build.name}</div>}
                                                            <div className={`text-[11px] mt-1 ${marginPct < 18 ? 'text-rose-700' : 'text-emerald-700'}`}>
                                                                Margin: {marginPct}% (cost ${cost.toFixed(0)})
                                                            </div>
                                                            <div className="flex gap-2 mt-2 text-xs">
                                                                <button onClick={() => setDealForm(d)} className="underline text-sky-600">Edit</button>
                                                                <button onClick={() => exportInvoicePdf(d)} className="underline text-indigo-600">Invoice PDF</button>
                                                                <button onClick={() => setDeals((prev) => prev.filter((x) => x.id !== d.id))} className="underline text-rose-600">Delete</button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                ) : n.id === 'ops' ? (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                                            <StatCard title="Orders (all)" value={`$${opsStats.orderSpend.toFixed(0)}`} accent="bg-indigo-500" />
                                            <StatCard title="Delivered spend" value={`$${opsStats.deliveredSpend.toFixed(0)}`} accent="bg-emerald-500" />
                                            <StatCard title="Deal revenue" value={`$${opsStats.dealRevenue.toFixed(0)}`} accent="bg-sky-500" />
                                            <StatCard title="Avg margin" value={`${opsStats.dealMargin}%`} accent="bg-amber-500" />
                                        </div>

                                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-semibold text-slate-800">What to order</h4>
                                                <span className="text-xs text-slate-500">{orderSuggestions.length} needs</span>
                                            </div>
                                            <div className="divide-y divide-slate-100">
                                                {orderSuggestions.length === 0 && <p className="text-sm text-slate-500 p-2">No shortages.</p>}
                                                {orderSuggestions.map((s) => {
                                                    const bestSup = suppliers
                                                        .map((sup) => {
                                                            const orderCount = orders.filter((o) => o.vendor === sup.name).length;
                                                            const delivered = orders.filter((o) => o.vendor === sup.name && o.status === 'Delivered').length;
                                                            const sla = orderCount ? delivered / orderCount : 0;
                                                            return { sup, sla };
                                                        })
                                                        .sort((a, b) => b.sla - a.sla)[0];
                                                    return (
                                                        <div key={s.inventory_id} className="py-2 flex items-center justify-between">
                                                            <div>
                                                                <div className="text-sm font-semibold text-slate-900">{s.label}</div>
                                                                <div className="text-xs text-slate-600">Need {s.missing} • Type {s.item_type}</div>
                                                                {bestSup && (
                                                                    <div className="text-[11px] text-slate-500">Try: {bestSup.sup.name} (SLA {(bestSup.sla * 100).toFixed(0)}%)</div>
                                                                )}
                                                            </div>
                                                            <div className="flex gap-2 text-xs">
                                                                <button onClick={() => prefillOrderFromShortage(s)} className="px-2 py-1 rounded border bg-white hover:border-sky-200">Prefill PO</button>
                                                                <button onClick={() => addRestockTask({ inventory_id: s.inventory_id, missing: s.missing, builds: s.builds || [], reason: s.label })} className="px-2 py-1 rounded border bg-white hover:border-amber-200">Task</button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-semibold text-slate-800">Profit quick look</h4>
                                                <span className="text-xs text-slate-500">{deals.length} deals</span>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                {deals.length === 0 && <p className="text-sm text-slate-500">No deals yet.</p>}
                                                {deals.map((d) => {
                                                    const build = builds.find((b) => b.id === d.buildId);
                                                    const cost = costForParts(build?.parts || []);
                                                    const sell = Number(d.amount || 0);
                                                    const margin = sell ? Math.round(((sell - cost) / sell) * 100) : 0;
                                                    return (
                                                        <div key={d.id} className="border border-slate-100 rounded-lg p-3">
                                                            <div className="flex items-center justify-between">
                                                                <div className="font-semibold text-slate-900">{d.name}</div>
                                                                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{d.stage}</span>
                                                            </div>
                                                            <div className="text-xs text-slate-600">{d.client || 'No client'} • ${sell.toFixed(0)}</div>
                                                            <div className={`text-xs mt-1 ${margin < 18 ? 'text-rose-700' : 'text-emerald-700'}`}>Margin {margin}% (cost ${cost.toFixed(0)})</div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                ) : n.id === 'prebuilts' ? (
                                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                                        <div className="xl:col-span-2 space-y-4">
                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                                <div className="flex items-center justify-between mb-3">
                                                    <div>
                                                        <p className="text-sm text-slate-500">Planned build</p>
                                                        <h3 className="text-xl font-semibold text-slate-800">{preBuiltForm.id ? 'Edit pre-built' : 'New pre-built'}</h3>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button onClick={() => setPreBuiltForm({ id: null, name: '', tier: '', targetUse: '', targetSell: '', taxPercent: 0, notes: '', parts: [] })} className="px-3 py-2 rounded-lg border text-slate-700 bg-white hover:bg-slate-50">Clear</button>
                                                        <button
                                                            onClick={() => {
                                                                const payload = { ...preBuiltForm, id: preBuiltForm.id || Date.now() };
                                                                setPreBuilts((prev) => {
                                                                    const idx = prev.findIndex((p) => p.id === payload.id);
                                                                    if (idx >= 0) {
                                                                        const copy = [...prev];
                                                                        copy[idx] = payload;
                                                                        return copy;
                                                                    }
                                                                    return [...prev, payload];
                                                                });
                                                                toast('Saved pre-built', true);
                                                            }}
                                                            className="px-3 py-2 rounded-lg bg-sky-500 text-white font-semibold shadow hover:bg-sky-600"
                                                        >
                                                            Save
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="grid md:grid-cols-2 gap-3">
                                                    <input value={preBuiltForm.name} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, name: e.target.value })} placeholder="Build name" className="border rounded-lg px-3 py-2" />
                                                    <input value={preBuiltForm.tier} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, tier: e.target.value })} placeholder="Tier (e.g., Budget / Mid / High)" className="border rounded-lg px-3 py-2" />
                                                    <input value={preBuiltForm.targetUse} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, targetUse: e.target.value })} placeholder="Target use (gaming, workstation...)" className="border rounded-lg px-3 py-2" />
                                                    <input value={preBuiltForm.targetSell} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, targetSell: e.target.value })} placeholder="Target sell price $" className="border rounded-lg px-3 py-2" />
                                                    <input value={preBuiltForm.taxPercent} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, taxPercent: e.target.value })} placeholder="Tax % (optional)" className="border rounded-lg px-3 py-2" />
                                                </div>
                                                <textarea value={preBuiltForm.notes} onChange={(e) => setPreBuiltForm({ ...preBuiltForm, notes: e.target.value })} placeholder="Notes" className="border rounded-lg px-3 py-2 w-full mt-3" rows="2" />
                                            </div>

                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Add part</h4>
                                                <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-2">
                                                    <input value={prePart.name} onChange={(e) => setPrePart({ ...prePart, name: e.target.value })} placeholder="Part name" className="border rounded px-3 py-2 text-sm" />
                                                    <select value={prePart.category} onChange={(e) => setPrePart({ ...prePart, category: e.target.value })} className="border rounded px-3 py-2 text-sm">
                                                        <option value="">Category</option>
                                                        {['CPU','GPU','Motherboard','RAM','Storage','PSU','Case','Cooler','Fans','OS','Other'].map((c) => <option key={c}>{c}</option>)}
                                                    </select>
                                                    <select value={prePart.vendor} onChange={(e) => setPrePart({ ...prePart, vendor: e.target.value })} className="border rounded px-3 py-2 text-sm">
                                                        <option value="">Vendor</option>
                                                        {['Amazon','eBay','Newegg','BestBuy','Other'].map((v) => <option key={v}>{v}</option>)}
                                                    </select>
                                                    <input value={prePart.link} onChange={(e) => setPrePart({ ...prePart, link: e.target.value })} placeholder="Buy link (URL)" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.cost} onChange={(e) => setPrePart({ ...prePart, cost: e.target.value })} placeholder="Cost $" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.shippingDays} onChange={(e) => setPrePart({ ...prePart, shippingDays: e.target.value })} placeholder="Ship days" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.qty} onChange={(e) => setPrePart({ ...prePart, qty: e.target.value })} placeholder="Qty" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.shipCost} onChange={(e) => setPrePart({ ...prePart, shipCost: e.target.value })} placeholder="Shipping cost (optional)" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.tax} onChange={(e) => setPrePart({ ...prePart, tax: e.target.value })} placeholder="Tax (optional)" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.condition} onChange={(e) => setPrePart({ ...prePart, condition: e.target.value })} placeholder="Condition" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.sku} onChange={(e) => setPrePart({ ...prePart, sku: e.target.value })} placeholder="SKU/ASIN (optional)" className="border rounded px-3 py-2 text-sm" />
                                                    <input value={prePart.notes} onChange={(e) => setPrePart({ ...prePart, notes: e.target.value })} placeholder="Notes (optional)" className="border rounded px-3 py-2 text-sm" />
                                                </div>
                                                <div className="flex justify-end mt-3">
                                                    <button onClick={addPrePart} className="px-3 py-2 rounded-lg bg-emerald-500 text-white text-sm font-semibold shadow hover:bg-emerald-600">Add part</button>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="text-sm font-semibold text-slate-800">Cost summary</h4>
                                                    <div className="text-xs text-slate-500">Latest arrival: {preBuiltTotals.latestArrivalDays || 0} days</div>
                                                </div>
                                                <div className="space-y-1 text-sm">
                                                    <div className="flex justify-between"><span>Parts subtotal</span><span>${preBuiltTotals.partsTotal.toFixed(2)}</span></div>
                                                    <div className="flex justify-between"><span>Tax</span><span>${preBuiltTotals.tax.toFixed(2)}</span></div>
                                                    <div className="flex justify-between font-semibold"><span>Total cost</span><span>${preBuiltTotals.total.toFixed(2)}</span></div>
                                                    <div className="flex justify-between"><span>Target sell</span><span>${Number(preBuiltTotals.sell || 0).toFixed(2)}</span></div>
                                                    <div className={`flex justify-between font-semibold ${preBuiltTotals.profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                                                        <span>Profit / margin</span>
                                                        <span>${preBuiltTotals.profit.toFixed(2)} ({preBuiltTotals.margin.toFixed(1)}%)</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 max-h-[480px] overflow-y-auto">
                                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Parts list</h4>
                                                {preBuiltForm.parts.length === 0 && <p className="text-sm text-slate-500">No parts added.</p>}
                                                <div className="space-y-2">
                                                    {preBuiltForm.parts.map((p) => (
                                                        <div key={p.id} className="border border-slate-100 rounded-lg p-2 text-sm">
                                                            <div className="flex justify-between">
                                                                <div>
                                                                    <div className="font-semibold text-slate-900">{p.name}</div>
                                                                    <div className="text-[11px] text-slate-500">{p.category} • {p.vendor}</div>
                                                                    {p.link && <a href={p.link} target="_blank" rel="noreferrer" className="text-xs text-sky-600 underline">Open link</a>}
                                                                </div>
                                                                <div className="text-right space-y-1">
                                                                    <div>${Number(p.cost || 0).toFixed(2)} x {p.qty || 1}</div>
                                                                    {p.shipCost && <div className="text-[11px] text-slate-500">Ship ${p.shipCost}</div>}
                                                                    {p.shippingDays && <div className="text-[11px] text-slate-500">ETA {p.shippingDays}d</div>}
                                                                </div>
                                                            </div>
                                                            <div className="flex justify-between mt-1 text-[11px] text-slate-500">
                                                                <div>{p.condition || 'Condition n/a'}</div>
                                                                <div>{p.notes || ''}</div>
                                                            </div>
                                                            <div className="flex justify-end mt-1">
                                                                <button onClick={() => removePrePart(p.id)} className="text-xs text-rose-600 underline">Remove</button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="text-sm font-semibold text-slate-800">Saved pre-builts</h4>
                                                    <span className="text-xs text-slate-500">{preBuilts.length} saved</span>
                                                </div>
                                                <div className="space-y-2 max-h-64 overflow-y-auto">
                                                    {preBuilts.length === 0 && <p className="text-sm text-slate-500">None yet.</p>}
                                                    {preBuilts.map((pb) => {
                                                        const partsTotal = (pb.parts || []).reduce((s, part) => s + (Number(part.cost) || 0) * (part.qty || 1) + (Number(part.shipCost) || 0), 0);
                                                        const sell = Number(pb.targetSell || 0);
                                                        const profit = sell - partsTotal;
                                                        return (
                                                            <div key={pb.id} className="border border-slate-100 rounded-lg p-2 text-sm flex items-center justify-between hover:border-sky-200">
                                                                <div>
                                                                    <div className="font-semibold text-slate-900">{pb.name}</div>
                                                                    <div className="text-[11px] text-slate-500">{pb.tier} • {pb.targetUse}</div>
                                                                    <div className="text-[11px] text-slate-500">Parts ${partsTotal.toFixed(0)} • Target ${sell.toFixed(0)} • Profit {profit >= 0 ? '+' : ''}${profit.toFixed(0)}</div>
                                                                </div>
                                                                <div className="flex gap-2 text-xs">
                                                                    <button onClick={() => setPreBuiltForm(pb)} className="underline text-sky-600">Open</button>
                                                                    <button
                                                                        onClick={() => {
                                                                            const clone = { ...pb, id: Date.now(), name: `${pb.name || 'Build'} (copy)` };
                                                                            setPreBuilts((prev) => [...prev, clone]);
                                                                            toast('Duplicated pre-built', true);
                                                                        }}
                                                                        className="underline text-indigo-600"
                                                                    >
                                                                        Duplicate
                                                                    </button>
                                                                    <button onClick={() => setPreBuilts((prev) => prev.filter((x) => x.id !== pb.id))} className="underline text-rose-600">Delete</button>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : n.id === 'profit' ? (
                                    <div className="space-y-4 w-full">
                                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                                            <StatCard title="Capital velocity" value={`$${profitEngine.capitalVelocity.toFixed(1)}/day`} accent="bg-indigo-500" />
                                            <StatCard title="Top item ROI/day" value={profitEngine.topItems[0] ? `$${profitEngine.topItems[0].profitPerDay.toFixed(1)}` : '$0'} accent="bg-emerald-500" />
                                            <StatCard title="Best build ROI" value={profitEngine.bestBuild ? `${profitEngine.bestBuild.roi.toFixed(0)}%` : '—'} accent="bg-amber-500" />
                                            <StatCard title="Inventory count" value={profitEngine.items.length} accent="bg-slate-500" />
                                        </div>
                                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-semibold text-slate-800">Today’s best move</h4>
                                                {profitEngine.bestBuild && (
                                                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">Build-first</span>
                                                )}
                                            </div>
                                            {profitEngine.bestBuild ? (
                                                <div className="text-sm text-slate-800">
                                                    Build: {profitEngine.bestBuild.build.name || profitEngine.bestBuild.build.id} • Expected profit ${profitEngine.bestBuild.profit.toFixed(0)} • ROI {profitEngine.bestBuild.roi.toFixed(0)}%
                                                    {profitEngine.bestBuild.issues?.length ? (
                                                        <div className="text-[11px] text-rose-700 mt-1">Needs: {profitEngine.bestBuild.issues.slice(0, 3).join(', ')}</div>
                                                    ) : (
                                                        <div className="text-[11px] text-emerald-700 mt-1">Ready to assemble.</div>
                                                    )}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-slate-500">No build stands out yet.</p>
                                            )}
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 h-full">
                                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Top items by profit/day</h4>
                                                <div className="space-y-2 text-sm">
                                                    {profitEngine.topItems.length === 0 && <p className="text-slate-500">No data.</p>}
                                                    {profitEngine.topItems.map((t) => (
                                                        <div key={t.item.inventory_id} className="flex justify-between">
                                                            <div>
                                                                <div className="font-semibold text-slate-900">{t.item.model || t.item.inventory_id}</div>
                                                                <div className="text-[11px] text-slate-500">{t.item.typeNormalized} • ROI {t.roi.toFixed(0)}%</div>
                                                            </div>
                                                            <div className="text-emerald-700 font-semibold">${t.profitPerDay.toFixed(1)}/day</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 h-full">
                                                <h4 className="text-sm font-semibold text-slate-800 mb-2">Decision cues</h4>
                                                <ul className="text-sm text-slate-700 space-y-1">
                                                    <li>🟢 BUILD NOW: ROI &gt; 40% and missing ≤ 1 cheap part.</li>
                                                    <li>🟡 HOLD: market trending up or waiting on GPU/CPU.</li>
                                                    <li>🔴 PART OUT: ROI &lt; 20% or days held &gt; 60.</li>
                                                    <li>🔥 PRIORITY LIST: highest profit/day first.</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                ) : n.id === 'tasks' ? (
                                    <div className="space-y-3">
                                        <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl">
                                            {tasks.length === 0 && <p className="p-3 text-sm text-slate-500">No tasks yet. Restock/ordered buttons on Shortages will add them here.</p>}
                                            {tasks.map((t) => (
                                                <div key={t.id} className="p-3 flex items-start justify-between">
                                                    <div>
                                                        <div className="font-semibold text-slate-900">{t.title}</div>
                                                        <div className="text-xs text-slate-500">{t.category} â€¢ {t.priority} â€¢ {t.created_at}</div>
                                                        <div className="text-xs text-slate-600">{t.notes}</div>
                                                    </div>
                                                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{t.status}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <ul className="text-slate-700 text-sm space-y-2">
                                        {n.id === 'shortages' && (
                                            <>
                                                <li>â€¢ Auto-list blockers from planned builds.</li>
                                                <li>â€¢ Track alternates (GPUs/PSUs/coolers).</li>
                                                <li>â€¢ Quick links to suppliers for re-order.</li>
                                            </>
                                        )}
                                        {n.id === 'orders' && (
                                            <>
                                                <li>â€¢ Quotes/invoices with status.</li>
                                                <li>â€¢ Payment due dates & fulfillment notes.</li>
                                                <li>â€¢ Tracking numbers / pickup info.</li>
                                            </>
                                        )}
                                        {n.id === 'inventory' && (
                                            <>
                                                <li>â€¢ Full stock database.</li>
                                                <li>â€¢ CSV import/export.</li>
                                                <li>â€¢ Low-stock automation.</li>
                                            </>
                                        )}
                                    </ul>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {thresholdModal && (
                    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-20">
                            <div className="bg-white rounded-2xl shadow-xl p-5 w-full max-w-md">
                                <h3 className="text-lg font-semibold mb-2">Low-stock rules</h3>
                                <p className="text-sm text-slate-600 mb-4">Set custom minimum quantities per item type. Default is 1; you can set 0 to disable alerts for a type.</p>
                                <form className="space-y-3" onSubmit={upsertThreshold}>
                                <div className="grid grid-cols-2 gap-2">
                                    <select
                                        value={newThreshold.type}
                                        onChange={(e) => setNewThreshold({ ...newThreshold, type: e.target.value })}
                                        className="border rounded-lg px-3 py-2"
                                >
                                    <option value="">Select item type</option>
                                    {['Components', 'Networking', 'Peripherals', 'Tools', 'Other'].map((group) => (
                                        <optgroup key={group} label={group}>
                                            {Object.keys(groupedOverview[group] || {}).sort().map((key) => (
                                                <option key={key} value={key}>{key}</option>
                                            ))}
                                        </optgroup>
                                    ))}
                                </select>
                                <input
                                    type="number"
                                    min="0"
                                    value={newThreshold.value}
                                    onChange={(e) => setNewThreshold({ ...newThreshold, value: e.target.value })}
                                    className="border rounded-lg px-3 py-2"
                                    placeholder="Min qty"
                                />
                            </div>
                                <div className="max-h-48 overflow-y-auto border rounded-lg p-2 text-sm text-slate-700 space-y-1">
                                    {thresholdList.map((key) => (
                                        <div key={key} className="flex items-center justify-between">
                                            <span className="capitalize">{key}</span>
                                            <span className="font-semibold">{thresholds[key] ?? defaultThreshold}</span>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <button type="button" onClick={() => setThresholdModal(false)} className="px-3 py-2 rounded-lg border bg-white">
                                        Cancel
                                    </button>
                                    <button type="submit" className="px-3 py-2 rounded-lg bg-sky-500 text-white">
                                        Save
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {detailItem && (
                    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-30">
                        <div className="bg-white rounded-2xl shadow-xl p-5 w-full max-w-lg">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-lg font-semibold text-slate-900">{detailItem.inventory_id}</h3>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            setEditingItem(detailItem);
                                            setFormData({ ...detailItem });
                                            setShowForm(true);
                                            setDetailItem(null);
                                        }}
                                        className="text-sky-600 hover:text-sky-700 text-sm underline"
                                    >
                                        Edit
                                    </button>
                                    <button onClick={() => setDetailItem(null)} className="text-slate-500 hover:text-slate-700">Close</button>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3 text-sm text-slate-800">
                                <div className="flex flex-col">
                                    <span className="font-semibold">Type:</span>
                                    <select
                                        value={detailItem.typeNormalized || ''}
                                        onChange={(e) => setDetailItem((d) => ({ ...d, typeNormalized: e.target.value }))}
                                        className="border rounded-lg px-2 py-1 mt-1"
                                    >
                                        <option value="">Select type</option>
                                        <optgroup label="Components">
                                            {['CPU', 'GPU', 'MOTHERBOARD', 'RAM', 'PSU', 'CASE', 'CPU COOLER', 'FAN', 'STORAGE', 'SSD', 'HDD'].map((t) => (
                                                <option key={t} value={t}>{t}</option>
                                            ))}
                                        </optgroup>
                                        <optgroup label="Networking">
                                            {['ROUTER', 'SWITCH', 'NIC', 'NETWORKING', 'ACCESS POINT', 'MODEM'].map((t) => (
                                                <option key={t} value={t}>{t}</option>
                                            ))}
                                        </optgroup>
                                        <optgroup label="Peripherals">
                                            {['KEYBOARD', 'MICE', 'KEYBOARD/MOUSE COMBO', 'MONITOR', 'WEBCAM', 'HEADSET', 'SPEAKER'].map((t) => (
                                                <option key={t} value={t}>{t}</option>
                                            ))}
                                        </optgroup>
                                        <optgroup label="Tools & Other">
                                            {['TOOL', 'ADAPTER', 'CABLE', 'THERMAL PASTE', 'OS', 'PSU CABLE', 'OTHER'].map((t) => (
                                                <option key={t} value={t}>{t}</option>
                                            ))}
                                        </optgroup>
                                    </select>
                                </div>
                                <div><span className="font-semibold">Status:</span> {detailItem.status}</div>
                                <div><span className="font-semibold">Brand:</span> {detailItem.brand}</div>
                                <div><span className="font-semibold">Model:</span> {detailItem.model}</div>
                                <div><span className="font-semibold">Qty:</span> {detailItem.qty}</div>
                                <div><span className="font-semibold">Socket (normalized):</span> {detailItem.socketNormalized || 'â€”'}</div>
                                <div><span className="font-semibold">Socket/Interface (raw):</span> {detailItem.socket_or_interface || 'â€”'}</div>
                                <div className="col-span-2"><span className="font-semibold">Storage subtype:</span> {detailItem.storageSubtype || 'â€”'}</div>
                                <div className="col-span-2"><span className="font-semibold">Details:</span> {detailItem.details || 'â€”'}</div>
                                <div><span className="font-semibold">Age:</span> {detailItem.ageDays != null ? `${detailItem.ageDays} days` : 'â€”'}</div>
                                <div className="col-span-2 text-xs text-slate-500">Source: {detailItem.source || 'â€”'} | Location: {detailItem.location_bin || ''} {detailItem.location_shelf || ''}</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InventoryList;

