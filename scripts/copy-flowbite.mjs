import { copyFileSync } from 'node:fs';
copyFileSync('node_modules/flowbite/dist/flowbite.min.js', 'static/js/flowbite.min.js');
copyFileSync('node_modules/flowbite/LICENSE.md', 'static/js/FLOWBITE-LICENSE.md');
