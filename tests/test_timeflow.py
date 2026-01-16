"""Tests for the unified time and event scheduling API."""

import pytest

from mesa import Agent, Model
from mesa.experimental.devs.eventlist import Priority


class TestScheduler:
    """Test the Scheduler class."""

    def test_schedule_at_absolute_time(self):
        """Test scheduling events at absolute times."""
        model = Model()

        results = []

        def callback():
            results.append(model.time)

        # Schedule events at different times
        model.schedule_at(callback, time=5)
        model.schedule_at(callback, time=3)
        model.schedule_at(callback, time=10)

        model.run_until(15)

        # Events should execute in time order
        assert results == [3, 5, 10]

    def test_schedule_after_relative_time(self):
        """Test scheduling events relative to current time."""
        model = Model()

        results = []

        def callback():
            results.append(model.time)

        # At t=0, schedule events
        model.schedule_after(callback, delay=5)
        model.schedule_after(callback, delay=3)

        model.run_until(10)

        assert results == [3, 5]

    def test_schedule_with_arguments(self):
        """Test scheduling events with arguments."""
        model = Model()

        results = []

        def callback(value, multiplier=1):
            results.append(value * multiplier)

        model.schedule_at(callback, time=1, args=[10], kwargs={"multiplier": 2})
        model.schedule_at(callback, time=2, args=[5])

        model.run_until(5)

        assert results == [20, 5]

    def test_schedule_with_priority(self):
        """Test that priority orders simultaneous events."""
        model = Model()

        results = []

        def callback(label):
            results.append(label)

        # Schedule three events at same time with different priorities
        model.schedule_at(callback, time=5, priority=Priority.LOW, args=["low"])
        model.schedule_at(callback, time=5, priority=Priority.HIGH, args=["high"])
        model.schedule_at(callback, time=5, priority=Priority.DEFAULT, args=["default"])

        model.run_until(10)

        # High priority first, then default, then low
        assert results == ["high", "default", "low"]

    def test_cancel_event(self):
        """Test canceling scheduled events."""
        model = Model()

        results = []

        def callback(label):
            results.append(label)

        event1 = model.schedule_at(callback, time=5, args=["event1"])
        event2 = model.schedule_at(callback, time=7, args=["event2"])
        model.schedule_at(callback, time=10, args=["event3"])

        # Cancel event1 and event2
        model.cancel_event(event1)
        model.cancel_event(event2)

        model.run_until(15)

        # Only event3 should execute
        assert results == ["event3"]

    def test_schedule_in_past_raises_error(self):
        """Test that scheduling in the past raises an error."""
        model = Model()
        model.time = 10

        with pytest.raises(ValueError, match="Cannot schedule event in the past"):
            model.schedule_at(lambda: None, time=5)


class TestRunControl:
    """Test the RunControl class."""

    def test_run_until(self):
        """Test running until a specific time."""
        model = Model()

        results = []

        def callback():
            results.append(model.time)

        model.schedule_at(callback, time=5)
        model.schedule_at(callback, time=15)
        model.schedule_at(callback, time=25)

        model.run_until(20)

        # Should execute events at t=5 and t=15, but not t=25
        assert results == [5, 15]
        assert model.time == 20

    def test_run_for(self):
        """Test running for a specific duration."""
        model = Model()

        results = []

        def callback():
            results.append(model.time)

        model.schedule_at(callback, time=5)
        model.schedule_at(callback, time=10)

        model.run_for(8)

        # Should execute event at t=5 but not t=10
        assert results == [5]
        assert model.time == 8

    def test_run_while(self):
        """Test running while a condition is true."""
        model = Model()

        counter = []

        def callback():
            counter.append(model.time)
            if len(counter) >= 3:
                model.running = False

        # Schedule events every 5 time units
        for i in range(1, 10):
            model.schedule_at(callback, time=i * 5)

        model.run_while(lambda m: m.running)

        # Should stop after 3 events
        assert len(counter) == 3
        assert counter == [5, 10, 15]

    def test_run_next_event(self):
        """Test executing events one at a time."""
        model = Model()

        results = []

        def callback(label):
            results.append(label)

        model.schedule_at(callback, time=5, args=["first"])
        model.schedule_at(callback, time=10, args=["second"])
        model.schedule_at(callback, time=15, args=["third"])

        # Execute events one by one
        assert model.run_next_event() is True
        assert results == ["first"]
        assert model.time == 5

        assert model.run_next_event() is True
        assert results == ["first", "second"]
        assert model.time == 10

        assert model.run_next_event() is True
        assert results == ["first", "second", "third"]
        assert model.time == 15

        # No more events
        assert model.run_next_event() is False

    def test_run_with_no_events(self):
        """Test running when no events are scheduled."""
        model = Model()

        model.run_until(10)
        assert model.time == 10

        model.run_for(5)
        assert model.time == 15


class TestStepIntegration:
    """Test integration of step() with the unified time API."""

    def test_step_auto_scheduled_with_run_for(self):
        """Test that step() is automatically scheduled when using run_for()."""

        class StepModel(Model):
            def __init__(self):
                super().__init__()
                self.step_count = 0

            def step(self):
                self.step_count += 1

        model = StepModel()
        model.run_for(5)

        # Step should be called at t=1, 2, 3, 4, 5
        assert model.step_count == 5
        assert model.steps == 5
        assert model.time == 5

    def test_step_with_scheduled_events(self):
        """Test that step() coexists with scheduled events."""

        class HybridModel(Model):
            def __init__(self):
                super().__init__()
                self.step_times = []
                self.event_times = []

                # Schedule an event
                self.schedule_at(self.special_event, time=3)

            def step(self):
                self.step_times.append(self.time)

            def special_event(self):
                self.event_times.append(self.time)

        model = HybridModel()
        model.run_for(5)

        # Step called at t=1, 2, 3, 4, 5
        assert model.step_times == [1, 2, 3, 4, 5]
        # Event called at t=3
        assert model.event_times == [3]

    def test_manual_step_deprecation_warning(self):
        """Test that manually calling step() triggers deprecation warning."""

        class SimpleModel(Model):
            def step(self):
                pass

        model = SimpleModel()

        with pytest.warns(FutureWarning, match="Calling model.step.*deprecated"):
            model.step()

    def test_manual_step_executes_events(self):
        """Test that manual step() still executes scheduled events."""

        class EventModel(Model):
            def __init__(self):
                super().__init__()
                self.event_executed = False
                self.schedule_at(self.event, time=1)

            def event(self):
                self.event_executed = True

        model = EventModel()

        with pytest.warns(FutureWarning):
            model.step()

        # Event at t=1 should have executed
        assert model.event_executed is True
        assert model.time == 1

    def test_empty_step_does_not_break(self):
        """Test that models without custom step() still work."""
        model = Model()  # No step override

        # Should not raise an error
        model.run_for(5)
        assert model.time == 5


class TestAgentSelfScheduling:
    """Test agents scheduling their own events."""

    def test_agent_schedules_own_event(self):
        """Test agents can schedule events for themselves."""

        class SchedulingAgent(Agent):
            def __init__(self, model):
                super().__init__(model)
                self.awake = True
                self.wake_count = 0

            def sleep(self, duration):
                self.awake = False
                self.model.schedule_after(self.wake_up, delay=duration)

            def wake_up(self):
                self.awake = True
                self.wake_count += 1

        model = Model()
        agent = SchedulingAgent(model)

        agent.sleep(5)
        assert agent.awake is False

        model.run_until(6)

        assert agent.awake is True
        assert agent.wake_count == 1

    def test_agent_chain_scheduling(self):
        """Test agents scheduling chains of events."""

        class ChainAgent(Agent):
            def __init__(self, model):
                super().__init__(model)
                self.events = []

            def start_chain(self):
                self.events.append(("start", self.model.time))
                self.model.schedule_after(self.middle, delay=5)

            def middle(self):
                self.events.append(("middle", self.model.time))
                self.model.schedule_after(self.end, delay=5)

            def end(self):
                self.events.append(("end", self.model.time))

        model = Model()
        agent = ChainAgent(model)

        agent.start_chain()
        model.run_until(20)

        assert agent.events == [
            ("start", 0),
            ("middle", 5),
            ("end", 10)
        ]


class TestPureEventDriven:
    """Test pure event-driven models without step()."""

    def test_event_driven_poisson_process(self):
        """Test a simple Poisson arrival process."""

        class ArrivalModel(Model):
            def __init__(self, arrival_rate):
                super().__init__()
                self.arrival_rate = arrival_rate
                self.arrivals = []

                # Bootstrap first arrival
                self.schedule_at(self.arrival, time=0)

            def arrival(self):
                self.arrivals.append(self.time)

                # Schedule next arrival
                next_time = self.time + self.random.expovariate(self.arrival_rate)
                self.schedule_at(self.arrival, time=next_time)

        model = ArrivalModel(arrival_rate=2.0)
        model.run_until(10.0)

        # Should have multiple arrivals
        assert len(model.arrivals) > 5
        # First arrival at t=0
        assert model.arrivals[0] == 0
        # All arrivals should be before t=10
        assert all(t <= 10 for t in model.arrivals)

    def test_event_driven_with_continuous_time(self):
        """Test that continuous time works correctly."""

        class ContinuousModel(Model):
            def __init__(self):
                super().__init__()
                self.event_times = []

                self.schedule_at(self.event, time=0.5)
                self.schedule_at(self.event, time=1.3)
                self.schedule_at(self.event, time=2.7)

            def event(self):
                self.event_times.append(self.time)

        model = ContinuousModel()
        model.run_until(5.0)

        assert model.event_times == [0.5, 1.3, 2.7]


class TestBackwardCompatibility:
    """Test backward compatibility with existing Mesa patterns."""

    def test_traditional_step_loop_works(self):
        """Test that traditional for-loop stepping still works."""

        class TraditionalModel(Model):
            def __init__(self):
                super().__init__()
                self.step_count = 0

            def step(self):
                self.step_count += 1

        model = TraditionalModel()

        # Traditional pattern
        with pytest.warns(FutureWarning):
            for _ in range(10):
                model.step()

        assert model.step_count == 10
        assert model.steps == 10

    def test_run_model_still_works(self):
        """Test that run_model() pattern still works."""

        class RunModel(Model):
            def __init__(self):
                super().__init__()
                self.step_count = 0

            def step(self):
                self.step_count += 1
                if self.step_count >= 5:
                    self.running = False

        model = RunModel()

        # This should use the manual step path
        with pytest.warns(FutureWarning):
            model.run_model()

        assert model.step_count == 5


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_schedule_at_current_time(self):
        """Test scheduling an event at or before the current time."""

        class TestModel(Model):
            def __init__(self):
                super().__init__()
                self.event_executed = False

            def test_event(self):
                self.event_executed = True

        model = TestModel()

        # Schedule event at time 1 (future)
        model.schedule_at(model.test_event, time=1)

        model.run_for(2)

        # Event at t=1 should execute
        assert model.event_executed is True

    def test_schedule_at_initial_time(self):
        """Test scheduling events at time 0 before any run."""

        class TestModel(Model):
            def __init__(self):
                super().__init__()
                self.results = []

            def event_a(self):
                self.results.append("a")

            def event_b(self):
                self.results.append("b")

        model = TestModel()

        # Schedule multiple events at the initial time
        model.schedule_at(model.event_a, time=0.5)
        model.schedule_at(model.event_b, time=1.5)

        model.run_until(2)

        assert model.results == ["a", "b"]

    def test_multiple_models_independent(self):
        """Test that multiple models have independent event lists."""

        class SimpleModel(Model):
            def __init__(self):
                super().__init__()
                self.events = []

            def event(self, label):
                self.events.append(label)

        model1 = SimpleModel()
        model2 = SimpleModel()

        model1.schedule_at(model1.event, time=5, args=["m1"])
        model2.schedule_at(model2.event, time=5, args=["m2"])

        model1.run_until(10)
        model2.run_until(10)

        assert model1.events == ["m1"]
        assert model2.events == ["m2"]

    def test_time_does_not_go_backward(self):
        """Test that time never decreases."""
        model = Model()

        times = []

        def record_time():
            times.append(model.time)

        model.schedule_at(record_time, time=5)
        model.schedule_at(record_time, time=3)
        model.schedule_at(record_time, time=10)

        model.run_until(15)

        # Times should be monotonically increasing
        assert times == sorted(times)

    def test_run_for_zero_duration(self):
        """Test running for zero duration."""
        model = Model()

        model.schedule_at(lambda: None, time=5)
        model.run_for(0)

        # Should not advance time or execute events
        assert model.time == 0

    def test_empty_event_list_run(self):
        """Test running with no events scheduled."""
        model = Model()  # No step override, no events

        model.run_until(100)

        # Should just advance time
        assert model.time == 100
