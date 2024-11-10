import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const DynamicBarChart: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const width = window.innerWidth; // Adjust to window width
    const height = 200; // Bar chart height
    const numBars = 30;
    const barWidth = width / numBars;

    // Generate random data initially (fixed positions on the x-axis)
    let data = Array.from({ length: numBars }, () => Math.random());

    // Array to store the direction of each bar (-1 for decreasing, 1 for increasing)
    let directions = Array.from({ length: numBars }, () => Math.random() < 0.5 ? -1 : 1);

    // Counter to keep track of how many periods have passed for each bar
    let counter = Array.from({ length: numBars }, () => 0);

    // Periods before changing direction (6 cycles)
    const period = 6;

    // Create the scales
    const x = d3.scaleLinear().domain([0, numBars]).range([0, width]);
    const y = d3.scaleLinear().domain([0, 1]).range([0, height]);

    // Set up the SVG element
    svg
      .attr('width', width)
      .attr('height', height)
      .style('position', 'absolute')
      .style('bottom', '0') // Stick to the bottom
      .style('left', '0')
      .style('z-index', '0');

    // Create bars (x is constant, only height/y varies)
    let bars = svg
      .selectAll('rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('x', (d, i) => x(i)) // x is fixed
      .attr('y', d => height - y(d)) // y varies based on height
      .attr('width', barWidth - 2)
      .attr('height', d => y(d)) // Initial height
      .attr('fill', d => `rgba(245, 245, 245, ${d})`); // Add transparency for a dynamic visual effect

    // Animation loop to simulate height variation effect
    function animateBars() {
      data = data.map((d, i) => {
        // Update the counter for each bar
        counter[i] += 1;

        // Every 6 periods, randomly decide whether the bar will increase or decrease its height
        if (counter[i] >= period) {
          counter[i] = 0; // Reset the counter after each period
          directions[i] = Math.random() < 0.5 ? -1 : 1; // Randomly set the direction
        }

        // Calculate new height based on the current direction
        let newHeight = d + directions[i] * 0.4; // Adjust the change factor (e.g., 0.05 for 5% change)

        // Ensure the new height is within [0, 1] range
        if (newHeight > 1) {
          newHeight = 1;
          directions[i] = -1; // If it exceeds, make it decrease
        } else if (newHeight < 0) {
          newHeight = 0;
          directions[i] = 1; // If it goes below, make it increase
        }

        return newHeight;
      });

      // Update bars with new data
      bars
        .data(data)
        .transition()
        .duration(1000) // Smooth movement
        .ease(d3.easeSinInOut) // Smooth transition for wave effect
        .attr('y', d => height - y(d)) // Update y position (height from bottom)
        .attr('height', d => y(d)) // Update height dynamically
        .attr('fill', d => `rgba(52, 152, 219, ${d})`); // Dynamic transparency
    }

    // Use d3.timer for continuous smooth animation
    d3.timer(animateBars);

    return () => d3.timerFlush(); // Clean up the timer on unmount
  }, []);

  return (
    <div style={{ position: 'fixed', bottom: 0, width: '100%', height: '200px', zIndex: 1 }}>
      <svg ref={svgRef} />
    </div>
  );
};

export default DynamicBarChart;
