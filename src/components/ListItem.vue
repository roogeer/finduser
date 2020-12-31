<template>
	<!-- <fragment> -->
		<tr :style="{backgroundColor:trbackcolor}">
			<td>{{index}}</td>
			<td>{{user.info.username}}</td>
			<td>{{user.info.userip}}</td>
			<td :class="user.info.pool">{{user.info.pool}}</td>
			<td>{{user.info.qos}}</td>
			
			<td>{{user.info.oltname}}</td>
			<td>{{user.info.oltip}}</td>
			<td>{{user.info.pevlan}}/{{user.info.cevlan}}</td>
			<td>{{user.info.onu}}</td>
			
			<td>{{user.info.brasname}}</td>
			<td>{{user.info.brasip}}</td>
			<td>{{user.info.interface}}</td>
			
			<td>{{user.info.hillstone}}</td>
			<td>{{user.info.panabit}}</td>
	
			<td align="left">{{user.info.detail}}</td>
		</tr>
	<!-- </fragment> -->
</template>

<script>
	// import  { Fragment } from 'vue-fragment'
	
	export default {
		name: 'ListItem',
		// components: { Fragment },
		props:{
			index: Number,
			user: Object,
			trbackcolor: String
		}
	}
</script>

<style scoped>
	.vip1 {
		background-color:darksalmon
	}
	.vip3 {
		background-color:crimson
	}
	.business {
		background-color:#007bff;
		color:gainsboro
	}
	.game {
		background-color:gold;
	}
	.iptv {
		background-color:cyan
	}
</style>
