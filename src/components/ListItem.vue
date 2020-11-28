<template>
	<!-- <fragment> -->
		<tr>
			<td>{{index}}</td>
			<td>{{user.username}}</td>
			<td>{{user.info.oltname}}</td>
			<td>{{user.info.oltip}}</td>
			<td>{{user.info.onu}}</td>
			<td>{{user.info.pevlan}}/{{user.info.cevlan}}</td>
			<td>{{user.info.nasportid}}</td>
			<td>{{user.info.detail}}</td>
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
			user: Object
		}
	}
</script>

<style>
</style>
