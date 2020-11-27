<template>
	<fragment>
		<tr>
<!-- 			<td :rowspan="totalRow" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()">{{index}}</td>
			<td :rowspan="totalRow" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()">{{ip}}</td>
			<td align="left" :rowspan="totalRow" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()">{{olt['name']}}</td>
			<td align="left" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()" :rowspan="olt['bras'][BrasKeys(olt)[0]]['interface'].length">{{olt['bras'][BrasKeys(olt)[0]]['name']}}</td>
			<td align="left" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()">{{olt['bras'][BrasKeys(olt)[0]]['interface'][0]}}</td>
			<td :rowspan="totalRow" align="left" :style="{backgroundColor:tdbgcolor}" @mouseenter="enter()"  @mouseleave="leave()" >{{olt['nasportid'].join(';')}}</td> -->
			<td>{{users[0].username}}</td>
		</tr>
	</fragment>
</template>

<script>
	import  { Fragment } from 'vue-fragment'
	
	export default {
		name: 'ListItem',
		components: { Fragment },
		props:{
			users: Array
		}
	}
</script>

<style>
</style>
