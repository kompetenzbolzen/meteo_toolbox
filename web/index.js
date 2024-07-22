// python3 -m http.server

const data_dir = 'data';
const index_file = "index.json";

var index = null;
var mapframe = null;

function httpGetAsync(url, callback)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}

function loadIndexFromJson(raw_text, title) {
	index_obj = JSON.parse(raw_text)
	//TODO pass index here. that would be cleaner than public vars.
	build_interface(index_obj, title);
}

function build_indexlist(index_obj, display_name) {
	div = document.createElement('div');
	div.classList.add('index');

	title = document.createElement('h4');
	title.innerText = display_name;
	div.appendChild(title);

	list = document.createElement('ul');

	for (const i in index_obj) {
		var map = index_obj[i];

		a = document.createElement('a');
		a.classList.add('link');
		a.setAttribute('href', '');// data_dir + '/' + map.file);
		a.setAttribute('mapfile', map.file);
		a.onclick = indexlink_click;
		a.innerText = map.display_name;
		a.id = map.file;

		li = document.createElement('li');
		li.appendChild(a);
		list.appendChild(li);

	}

	div.appendChild(list);
	return div;
}

function indexlink_click(e) {
	mapframe.querySelector('#mapframe').src = data_dir + '/' + this.getAttribute('mapfile');
	return false;
}

function productlink_click(e) {
	clear_interface();

	var list_title = this.getAttribute('list_title');

	httpGetAsync(data_dir + '/' + this.getAttribute('indexfile'), function(a){ loadIndexFromJson(a,list_title);});
	return false;
}

function build_mapframe() {
	div = document.createElement('div');
	div.classList.add('mapframe');
	frame = document.createElement('img');
	frame.id = 'mapframe';
	//frame.classList.add('mapframe');
	mapframe = frame;
	div.appendChild(frame);

	return div;
}

function build_interface(index_obj, display_name) {
	index = build_indexlist(index_obj, display_name);
	mapframe = build_mapframe();

	document.body.appendChild(index);
	document.body.appendChild(mapframe);
}

function clear_interface() {
	if (index)
		index.remove();
	if(mapframe)
		mapframe.remove();
}

function build_product_index(raw_text) {
	product_index = JSON.parse(raw_text);

	div = document.createElement('div');
	div.classList.add('product_index');

	title = document.createElement('h4');
	title.innerText = 'Products';
	div.appendChild(title);

	list = document.createElement('ul');

	for (const i in product_index) {
		var product = product_index[i];
		a = document.createElement('a');
		a.classList.add('link');
		a.setAttribute('href', '');// data_dir + '/' + map.file);
		a.setAttribute('indexfile', product.indexfile);
		a.setAttribute('list_title', product.list_title);
		a.onclick = productlink_click;
		a.innerText = product.name;
		a.id = product.indexfile;

		li = document.createElement('li');
		li.appendChild(a);
		list.appendChild(li);
	}

	div.appendChild(list);

	document.body.appendChild(div);
}

window.onload = function() {
	//httpGetAsync(data_dir + '/' + index_file, loadIndexFromJson);
	httpGetAsync(data_dir + '/' + index_file, build_product_index);
}
